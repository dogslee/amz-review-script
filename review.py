import asyncio
import json
import os
from playwright.async_api import async_playwright

# 统一输出目录（截图与评论数据均保存在此）
OUTPUT_DIR = "output"


def _reviews_url(
    locale: str,
    asin: str,
    page_num: int,
    filter_by_star: str | None,
) -> str:
    """拼评论页 URL，支持按星级筛选。"""
    base = f"https://www.amazon.{locale}/product-reviews/{asin}"
    params = f"pageNumber={page_num}&sortBy=recent"
    if filter_by_star and filter_by_star.lower() != "all":
        params += f"&filterByStar={filter_by_star.strip().lower()}"
    if page_num > 1:
        return f"{base}/ref=cm_cr_getr_d_paging_btm_next_{page_num}?{params}"
    return f"{base}?{params}"


async def get_amazon_reviews(
    asin: str,
    pages: int = 3,
    locale: str = "com",
    output_dir: str = OUTPUT_DIR,
    save_screenshots: bool = False,
    filter_by_star: str | None = "one_star",
):
    """
    爬取亚马逊商品评论

    :param asin:            商品 ASIN 码
    :param pages:           爬取页数
    :param locale:          站点后缀，如 com / co.jp / co.uk
    :param output_dir:      截图与数据的输出目录
    :param save_screenshots: 是否保存每页调试截图，默认 False
    :param filter_by_star:  按星级筛选：one_star/two_star/three_star/four_star/five_star/positive/critical，传 "all" 或不传则不过滤
    """
    if not os.path.exists("amazon_state.json"):
        print("❌ 未找到登录状态文件 amazon_state.json，请先运行 step1_login.py")
        return []

    os.makedirs(output_dir, exist_ok=True)
    all_reviews = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # 调试阶段保持 False，稳定后可改为 True
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
            ],
        )

        context = await browser.new_context(
            storage_state="amazon_state.json",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )

        # 隐藏 webdriver 特征
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

        page = await context.new_page()

        for page_num in range(1, pages + 1):
            url = _reviews_url(locale, asin, page_num, filter_by_star)
            print(f"\n{'='*60}")
            print(f"正在抓取第 {page_num} 页：{url}")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"❌ 页面加载失败：{e}")
                break

            # 等待页面渲染
            await asyncio.sleep(4)

            # 检查是否跳转到登录页
            if "signin" in page.url or "sign-in" in page.url:
                print("❌ 登录状态已过期，请重新运行 step1_login.py")
                break

            # 检查验证码
            captcha = await page.query_selector("form[action='/errors/validateCaptcha']")
            if captcha:
                print("⚠️  触发验证码，请在浏览器中手动完成，完成后按 Enter 继续...")
                input()

            # 打印页面标题确认
            title = await page.title()
            print(f"页面标题：{title}")

            # 分段滚动触发懒加载
            for ratio in [0.25, 0.5, 0.75, 1.0]:
                await page.evaluate(
                    f"window.scrollTo(0, document.body.scrollHeight * {ratio})"
                )
                await asyncio.sleep(0.8)

            # 滚回顶部
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)

            # 可选：保存调试截图到统一输出目录
            if save_screenshots:
                screenshot_path = os.path.join(output_dir, f"debug_page_{page_num}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 截图已保存：{screenshot_path}")

            # 等待评论元素出现
            try:
                await page.wait_for_selector("div[data-hook='review']", timeout=10000)
            except Exception:
                print("⚠️  等待评论元素超时，尝试继续...")

            # 尝试多个选择器
            review_elements = await page.query_selector_all("div[data-hook='review']")
            if not review_elements:
                review_elements = await page.query_selector_all("[data-hook='review']")
            if not review_elements:
                review_elements = await page.query_selector_all(".review")

            print(f"找到评论数量：{len(review_elements)}")

            if not review_elements:
                # 打印评论区 HTML 辅助排查
                html_snippet = await page.evaluate(
                    "document.querySelector('#cm_cr-review_list')?.innerHTML?.slice(0, 800) || '评论容器未找到'"
                )
                print(f"评论区 HTML 片段：\n{html_snippet}")
                print("已到最后一页或页面结构异常，停止抓取。")
                break

            # 解析每条评论
            page_reviews = []
            for el in review_elements:
                async def get_text(selector, parent=el):
                    node = await parent.query_selector(selector)
                    return (await node.inner_text()).strip() if node else "N/A"

                reviewer = await get_text("span.a-profile-name")

                # 评分（尝试多个选择器）
                rating_node = await el.query_selector(
                    "i[data-hook='review-star-rating'] span.a-icon-alt"
                )
                if not rating_node:
                    rating_node = await el.query_selector(
                        "i[data-hook='cmps-review-star-rating'] span.a-icon-alt"
                    )
                rating = (await rating_node.inner_text()).strip() if rating_node else "N/A"

                # 标题（尝试多个选择器）
                title_node = await el.query_selector(
                    "a[data-hook='review-title'] span:not(.a-icon-alt)"
                )
                if not title_node:
                    title_node = await el.query_selector("span[data-hook='review-title']")
                review_title = (await title_node.inner_text()).strip() if title_node else "N/A"

                date      = await get_text("span[data-hook='review-date']")
                body_node = await el.query_selector("span[data-hook='review-body'] span")
                if not body_node:
                    body_node = await el.query_selector("span[data-hook='review-body']")
                body = (await body_node.inner_text()).strip() if body_node else "N/A"

                verified  = await el.query_selector("span[data-hook='avp-badge']")
                helpful   = await get_text("span[data-hook='helpful-vote-statement']")

                review = {
                    "reviewer": reviewer,
                    "rating": rating,
                    "title": review_title,
                    "date": date,
                    "body": body,
                    "verified_purchase": "是" if verified else "否",
                    "helpful": helpful,
                }
                page_reviews.append(review)

            all_reviews.extend(page_reviews)
            print(f"✅ 本页成功抓取 {len(page_reviews)} 条评论，累计 {len(all_reviews)} 条")

            # 随机延迟，避免触发反爬
            await asyncio.sleep(3)

        await browser.close()

    return all_reviews


def print_reviews(reviews: list):
    print(f"\n{'='*60}")
    print(f"共抓取 {len(reviews)} 条评论")
    print(f"{'='*60}")
    for i, r in enumerate(reviews, 1):
        print(f"\n[{i}] 评论者：{r['reviewer']}")
        print(f"    评分：{r['rating']}")
        print(f"    标题：{r['title']}")
        print(f"    日期：{r['date']}")
        print(f"    认证购买：{r['verified_purchase']}")
        print(f"    有用票数：{r['helpful']}")
        body = r['body']
        print(f"    内容：{body[:300]}{'...' if len(body) > 300 else ''}")


def save_to_json(reviews: list, output_dir: str = OUTPUT_DIR, filename: str = "reviews.json"):
    path = os.path.join(output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 数据已保存至 {path}")


def save_to_csv(reviews: list, output_dir: str = OUTPUT_DIR, filename: str = "reviews.csv"):
    import csv
    if not reviews:
        return
    path = os.path.join(output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=reviews[0].keys())
        writer.writeheader()
        writer.writerows(reviews)
    print(f"✅ 数据已保存至 {path}")


if __name__ == "__main__":
    # ========== 配置区 ==========
    ASIN             = "B0CG5FTHT9"  # 替换为目标商品 ASIN
    PAGES            = 2             # 爬取页数（每页约10条）
    LOCALE           = "com"        # 站点：com / co.jp / co.uk / de 等
    OUTPUT_DIR       = "output"     # 截图与评论数据统一输出目录
    SAVE_SCREENSHOTS = False        # 是否保存每页调试截图（默认不保存）
    # 按星级筛选：one_star / two_star / three_star / four_star / five_star / positive / critical，设为 "all" 抓全部
    FILTER_BY_STAR   = "one_star"
    # ============================

    reviews = asyncio.run(
        get_amazon_reviews(
            asin=ASIN,
            pages=PAGES,
            locale=LOCALE,
            output_dir=OUTPUT_DIR,
            save_screenshots=SAVE_SCREENSHOTS,
            filter_by_star=FILTER_BY_STAR,
        )
    )

    if reviews:
        print_reviews(reviews)
        save_to_json(reviews, output_dir=OUTPUT_DIR)
        save_to_csv(reviews, output_dir=OUTPUT_DIR)
    else:
        print("未抓取到任何评论，请检查截图和日志排查原因。")