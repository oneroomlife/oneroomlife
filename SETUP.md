# oneroomlife · GitHub Profile 部署说明

版式参考 [BEPb/BEPb](https://github.com/BEPb/BEPb)：渐变横幅 → 徽章行 → 打字机 → 贡献热力图 → 数据面板 → 摸鱼蛇 / 3D 贡献图 → B 站入口 → 访客计数器 → Star History → 页脚波浪。

**设计原则：页面不依赖第三方图床。** 横幅、分隔、页脚、B 站按钮、贡献热力图、数据面板全部是本仓库自己的 SVG，随时打开都能显示；只保留 shields.io、typing-svg、streak-stats、count.getloli、star-history 这类长期稳定的公共接口。

## 1. 目录结构

```
oneroomlife-profile/
├── README.md                          # 主页正文（放仓库根目录）
├── SETUP.md                           # 本文
├── assets/
│   ├── header.svg                     # 顶部横幅：四层无缝位移波浪 + 上浮气泡（SMIL）
│   ├── divider.svg                    # 章节分隔波纹
│   ├── footer.svg                     # 页脚：心形呼吸 + 四层波浪 + 气泡
│   ├── bilibili.svg                   # B 站跳转按钮
│   ├── contribution-graph.svg         # 贡献热力图 · 浅色（脚本生成）
│   ├── contribution-graph-dark.svg    # 贡献热力图 · 深色
│   ├── stats.svg                      # 数据面板 · 浅色
│   └── stats-dark.svg                 # 数据面板 · 深色
├── scripts/
│   └── gen_assets.py                  # 抓 GitHub 公开数据 → 生成上面 4 张图
└── .github/workflows/
    ├── assets.yml                     # 每天刷新热力图 / 数据面板并提交
    ├── snake.yml                      # 生成摸鱼蛇 → output 分支
    └── profile-3d.yml                 # 生成 3D 贡献图 → profile-3d-contrib/
```

## 2. 三步上线

```bash
# 1) 克隆（或网页上先建一个同名仓库 oneroomlife/oneroomlife）
git clone https://github.com/oneroomlife/oneroomlife.git
cd oneroomlife

# 2) 把这套文件拷进去（README.md、SETUP.md、assets/、scripts/、.github/）
#    注意 README.md 会覆盖同名文件，先备份

# 3) 推送
git add -A
git commit -m "feat(profile): 渐变横幅 + 自绘热力图 + 动画蛇 + B 站入口"
git push
```

> 仓库名必须与用户名完全一致（`oneroomlife/oneroomlife`），GitHub 才会把它当 Profile 仓库渲染。

## 3. 三个工作流

| 工作流 | 产物 | 触发 | 首次需要 |
| --- | --- | --- | --- |
| `assets.yml` | `assets/contribution-graph*.svg`、`assets/stats*.svg`（提交回 main） | 每天 00:15 UTC、push、手动 | 无（`assets/` 里已有初始版本，直接能显示） |
| `snake.yml` | `output` 分支下 `github-snake.svg` / `github-snake-dark.svg` | 每天 00:00 UTC、push、手动 | 手动 Run 一次，否则蛇图 404 |
| `profile-3d.yml` | `profile-3d-contrib/profile-night-rainbow.svg`（提交回 main） | 每天 00:30 UTC、push、手动 | 手动 Run 一次，否则 3D 图 404 |

先在 **Settings → Actions → General → Workflow permissions** 选 **Read and write permissions** 并保存，否则三个工作流都没法回写仓库。

## 4. 本地重新生成图表

```bash
GITHUB_TOKEN=xxx python scripts/gen_assets.py --user oneroomlife --out assets
```

- 只依赖 Python 3.10+ 标准库，没有 pip 依赖。
- 先试 `urllib`，握手失败会自动退回系统 `curl`（国内网络常见）。
- 数据来源：`https://github.com/users/<user>/contributions`（日历格子）+ `api.github.com`（星标、Fork、仓库、语言字节数）。
- 有没有 `GITHUB_TOKEN` 都能跑，带上只是为了避免 API 限流。

## 5. 需要按需改的点

| 位置 | 现在的内容 | 改法 |
| --- | --- | --- |
| `README.md` 里的 `oneroomlife` | 用户名 | 全局替换（徽章、图表、raw 链接都要换） |
| `README.md` 里的 `448794468` | B 站 UID | 换成自己的：`https://space.bilibili.com/<UID>` |
| `scripts/gen_assets.py` 的 `--user` | `oneroomlife` | workflow 里改成 `--user 你的用户名`，或直接用默认值改这里 |
| `assets/header.svg` | 渐变 `#dcc4ef → #b8c1ee → #b4cff3`，文案 `AZUR LANE · ANDROID · ELECTRON` | 改 `<stop stop-color>`；文案改 `<text>`；主标题字号 92 时横向覆盖 86%，长文案要同时调小 |
| `assets/bilibili.svg` | 副标题 `space.bilibili.com/448794468` | 改 `<text>`；按钮宽 320 已按最长文案排版 |
| typing SVG | 5 行自我介绍 | 改 URL 的 `lines=`，中文要 URL 编码，`;` 分隔多行 |
| `count.getloli.com` | `@oneroomlife.github.readme` | 改 `@用户名.github.readme`，`theme` 可换 `moebooru` / `konachan` / `gelbooru` / `asoul` |
| 横幅文案 | `assets/header.svg` 里的主标题 `<text>`（改完直接推，raw 直连即时生效） | 改字号要同步调 `y` 基线 |

## 6. 常见问题

- **热力图 / 数据面板是旧的**：`assets.yml` 每天跑一次；想立刻刷新就手动 Run 该工作流，或本地跑一次 `gen_assets.py` 再提交。
- **热力图空白或格子错位**：GitHub 改了 `users/<user>/contributions` 的 HTML 结构时，`gen_assets.py` 会抛 `贡献日历解析失败`，按新的 `data-date` / `data-level` 属性调整正则即可。
- **蛇图 404 / 3D 图 404**：对应工作流还没跑过。跑一次，等 1–2 分钟。
- **图片被 camo 缓存**：GitHub 会缓存外链图片。改 URL 参数（如 `&v=2`）或换一次 commit。
- **streak / star-history 空白**：这两个是公共实例，偶尔限流，等几分钟重试。
- **深色模式**：横幅、页脚、B 站按钮是浅色渐变，深色下同样成立；热力图与数据面板有 `-dark` 版本，README 用 `<picture>` 自动切换。
- **`style=` 属性**：GitHub 会剥离 README 里的 `style`，所以版式只用 `align` / `width` / `valign` 这类属性控制。
- **图片地址是绝对 raw 链接**：所有图（含 `assets/*.svg`）都写成 `https://raw.githubusercontent.com/oneroomlife/oneroomlife/main/assets/xxx.svg`，好处是 profile 页和仓库页行为一致、不受相对路径解析影响。代价是**换用户名或换默认分支名（main→master）时必须全局替换**，否则全图 404。

## 7. 本地预览

```bash
# 单张图直接看
start assets/header.svg

# 整页预览：README 里的图片是绝对 raw 链接，本地渲染会 404。
# 先转成相对路径再看：
npx marked README.md -o preview.html
# 然后把 preview.html 里的
#   https://raw.githubusercontent.com/oneroomlife/oneroomlife/main/
# 替换成 ./
```

放宽到 GitHub 的实际内容宽度（约 860px）看一眼，能提前发现换行、徽章挤压之类的问题。
