# 亚马逊商品评论抓取工具

本工具用于在**已登录亚马逊账号**的前提下，自动抓取指定商品的用户评论，并导出为 JSON 和 CSV 文件，方便做数据分析或备份。

**适合谁用**：不需要会写代码，只要会按步骤在电脑上打开终端、运行命令即可。

---

## 一、这个工具能做什么？

1. **第一步（登录）**：打开一个浏览器窗口，你在里面手动登录亚马逊账号；程序会记住你的登录状态，下次不用再输密码。
2. **第二步（抓评论）**：你只需提供一个商品的 **ASIN 码**（在亚马逊商品页链接里能看到），程序会自动打开页面、翻页，把评论抓下来，保存成：
   - `reviews.json`（适合程序读取）
   - `reviews.csv`（适合用 Excel 打开）

---

## 二、使用前需要准备什么？

- **电脑**：Windows / macOS / Linux 均可。
- **网络**：能正常打开 [亚马逊](https://www.amazon.com)（若用其他站点如日亚、英亚，后面会说明如何改）。
- **uv**：一个用来安装和运行本项目的工具（见下一节）。
- **Python 3.12 或更高**：uv 会自动处理，一般不需要你单独装 Python。

---

## 三、安装 uv（如果还没装）

**uv** 是一个快速的 Python 项目运行工具，用来安装依赖和运行脚本。

- **Windows**（在 PowerShell 里执行）：
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **macOS / Linux**：
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

安装完成后，**新开一个终端窗口**，输入 `uv --version`，能看到版本号就说明安装成功。

---

## 四、安装本项目与 Playwright 浏览器

1. **打开终端**  
   - Windows：在开始菜单搜「PowerShell」或「终端」并打开。  
   - macOS：打开「终端」或「iTerm」。  
   - Linux：打开你常用的终端（如 Terminal）。

2. **进入项目文件夹**  
   在终端里输入（把路径改成你电脑上 `tu` 项目所在位置）：
   ```bash
   cd /Users/xiang.lilx/Desktop/tu
   ```
   Windows 示例：`cd C:\Users\你的用户名\Desktop\tu`

3. **用 uv 安装项目依赖**  
   在项目目录下执行：
   ```bash
   uv sync
   ```
   这会根据 `pyproject.toml` 自动创建虚拟环境并安装 Python 依赖（包括 Playwright 的 Python 包）。

4. **安装 Playwright 的浏览器（重要）**  
   Playwright 除了 Python 包，还需要下载一个「浏览器」才能自动打开网页。在**同一项目目录**下执行：
   ```bash
   uv run playwright install chromium
   ```
   会下载 Chromium 浏览器，通常只需执行一次。若希望安装所有浏览器（Chromium、Firefox、WebKit），可执行：
   ```bash
   uv run playwright install
   ```

---

## 五、使用步骤

### 步骤 1：保存亚马逊登录状态（首次使用必做）

在项目目录下执行：

```bash
uv run python login.py
```

- 会自动弹出一个**浏览器窗口**，并打开亚马逊登录页。
- 请在浏览器里**像平时一样登录**你的亚马逊账号（含验证码、两步验证等）。
- 登录成功后，回到**终端**，按一下 **Enter（回车）**。
- 程序会把登录状态保存到当前目录的 `amazon_state.json`。  
  下次抓评论时会自动用这个文件，一般不需要再次运行本步骤，除非登录过期或被登出。

### 步骤 2：抓取商品评论

在项目目录下执行：

```bash
uv run python review.py
```

- 默认会抓取 `review.py` 里配置好的那个商品的评论（多页），并生成：
  - `reviews.json`
  - `reviews.csv`
- 抓取时可能还会弹出浏览器窗口（便于处理验证码等），若出现验证码，在浏览器里完成后再回到终端按 Enter。

**想抓别的商品或改页数、站点？**  
用记事本或任意编辑器打开 `review.py`，找到文件末尾的「配置区」：

```python
ASIN   = "B0CG5FTHT9"  # 改成你要的商品 ASIN
PAGES  = 5             # 要抓取的页数（每页约 10 条）
LOCALE = "com"         # 站点：com=美亚, co.jp=日亚, co.uk=英亚, de=德亚 等
```

- **ASIN**：在亚马逊商品页的网址里，`/dp/B0CG5FTHT9` 这种 `B0...` 或 `B1...` 的 10 位码就是 ASIN。  
- 改好后保存文件，再执行一次 `uv run python review.py` 即可。

---

## 六、输出文件说明

| 文件 | 说明 |
|------|------|
| `amazon_state.json` | 登录状态（cookie 等），不要分享给他人。 |
| `reviews.json` | 评论的完整数据，UTF-8 编码，适合程序读取。 |
| `reviews.csv` | 同上内容，表格形式，可用 Excel、WPS 打开。 |
| `debug_page_1.png` 等 | 抓取时的页面截图，用于排查问题，可删除。 |

---

## 七、常见问题

- **提示「未找到登录状态文件 amazon_state.json」**  
  请先完成「步骤 1」运行一次 `uv run python login.py` 并成功保存登录状态。

- **提示「登录状态已过期」或又跳回登录页**  
  重新执行步骤 1，再次登录并保存状态。

- **出现验证码**  
  程序会提示你在弹出的浏览器里手动完成验证码，完成后在终端按 Enter 继续。

- **`uv run playwright install chromium` 很慢或失败**  
  可能是网络问题，可多试几次，或换网络/使用代理后再执行。

- **没有 Python / 不知道 Python 是什么**  
  只要按上面步骤安装好 uv，并在项目目录里用 `uv run python ...` 运行脚本即可，不需要单独安装 Python。

---

## 八、简要命令速查

在**项目目录**下：

| 目的 | 命令 |
|------|------|
| 首次安装依赖 | `uv sync` |
| 安装 Playwright 浏览器（首次必做） | `uv run playwright install chromium` |
| 保存亚马逊登录状态（首次或过期时） | `uv run python login.py` |
| 抓取评论 | `uv run python review.py` |

---

## 九、技术说明（可选阅读）

- 本项目使用 **Python 3.12+**，依赖 **Playwright** 做浏览器自动化，**Beautiful Soup** 与 **requests** 在依赖列表中。
- 使用 **uv** 管理虚拟环境与依赖，所有运行命令均通过 `uv run` 在项目虚拟环境中执行。
- 登录状态保存在本地 `amazon_state.json`，仅用于本机抓取，请勿上传或分享。

如有问题，可查看运行时的终端输出或 `debug_page_*.png` 截图辅助排查。
