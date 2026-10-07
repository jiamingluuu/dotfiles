# Goofy Preview 目录结构说明

`goofy preview deploy` 按优先级自动识别目录类型并生成部署配置，支持直接传入项目根目录或构建产物目录。

## 目录类型（按识别优先级）

### 1. 带 deploy.yml 的项目

根目录含 `deploy.yml`（Goofy 定义的部署配置文件协议），直接按配置部署。

```
my-project/
├── deploy.yml          # Goofy 部署配置文件
├── html/               # 静态资源或 SSR 入口（按 deploy.yml 配置）
│   └── main/
│       └── index.html
└── ...
```

适用场景：已有完整 `deploy.yml` 配置的项目、自定义路由规则、非纯静态站点。

**部署示例：**
```bash
bytedcli goofy preview deploy my-project --alias my-custom-app
```

### 2. Next.js 静态导出

识别到 `.next/` 目录（含 `static/` 和 `server/app` / `server/pages` 下的 HTML），
自动整理 HTML 与静态资源，生成适配 Next.js 的路由规则。

**传入项目根目录（推荐）：**
```
my-next-app/
├── .next/
│   ├── static/
│   └── server/
│       ├── app/
│       │   └── index.html
│       └── pages/
├── public/             # 可选，会被一并拷贝
│   └── favicon.ico
├── package.json
└── next.config.js
```

**直接传入 .next 目录：**
```
.next/
├── static/
└── server/
    ├── app/
    │   └── index.html
    └── pages/
```

适用场景：Next.js 项目的 `next build` 产物（SSG 页面或 `output: 'export'`）。

> 只支持纯静态 HTML 页面，不支持 SSR 模式。

**部署示例：**
```bash
next build
bytedcli goofy preview deploy . --alias my-next-app
```

### 3. 纯静态站点

根目录含 `index.html`，且不含 `deploy.yml` / `.next` / `package.json` / `src` / `node_modules` 等源码标记。CLI 自动生成 `deploy.yml`，以 `worker` 模式部署。

```
dist/
├── index.html
├── assets/
│   ├── index.abc123.js
│   └── style.def456.css
└── favicon.ico
```

适用场景：Vite / Webpack / Rollup 等构建出的纯静态产物、静态 HTML 页面。

> 如果目录下同时存在 `package.json` 或 `src/`，CLI 会认为这是源码目录而非构建产物，会拒绝部署并提示先构建。

**部署示例：**
```bash
# Vite 项目（产物在 dist/）
npm run build
bytedcli goofy preview deploy dist --alias my-vite-app

# CRA 项目（产物在 build/）
npm run build
bytedcli goofy preview deploy build --alias my-react-app
```

## 自动检测机制

如果传入的是项目根目录（包含 `package.json` / `src` 等源码标记），CLI 会依次
查找 `dist/`、`build/`、`out/` 三个常见构建产物目录；找到符合"纯静态站点"
结构的子目录后，再递归执行目录识别。

```
my-project/             # 传入这个目录
├── package.json
├── src/
│   └── index.ts
└── dist/               # CLI 会自动找到并部署这个目录
    ├── index.html
    └── assets/
```

适用场景：直接在项目根目录执行 `goofy preview deploy .`，不用手动指定构建产物路径。

## 部署限制

- **包体大小**：打包后 tarball 不超过 50 MB，超出需清理后重试
- **忽略文件**：`.DS_Store` 会被自动排除
- **alias 规则**：只允许字母、数字、连字符，不能以 `-` 开头；也支持传完整的 `*.gf-preview.bytedance.net` 域名
- **默认过期时间**：365 天，可通过 `--expiry-days` 调整

## 错误排查

- **"Could not detect a deployable build output"**：目录既没有 `index.html` 也没有 `deploy.yml`
  - 源码目录请先执行构建（如 `npm run build`）
  - 构建产物目录请确认根目录下存在 `index.html`
- **"This looks like a project source directory"**：识别到源码标记但没找到构建产物，请先执行构建
- **Tarball exceeds 50MB**：包体过大，清理 `node_modules`、source map 或其他大文件后重试
