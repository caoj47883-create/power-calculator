# 功耗计算器 · iOS / Xcode 工程

这是 Android 同款离线页面的 iOS 原生壳：**SwiftUI + WKWebView**。界面、字体、浅色主题、首次身体资料、单卡三态固定、周边五档评价和历史记录与 Android v2.1 保持一致。

> **重要限制**：这个工程是在 Windows 上生成的，当前环境没有 macOS / Xcode，因此**没有在本机编译、签名，也没有在本机生成 IPA**。需要在 Mac 上用 Xcode 15+ 打开后构建；要装到真机或上 TestFlight，还需要你自己的 Apple Developer Team。
>
> 没有 Mac、但有 Windows 电脑的话，可以用本工程自带的 GitHub Actions workflow 在云端 macOS 上构建未签名 IPA，再用 Windows 上的 Sideloadly 自签安装。详细步骤见 [`WINDOWS-SIDELOAD.md`](WINDOWS-SIDELOAD.md)。

## 快速运行

1. 解压后在 Mac 上双击 `PowerLedger.xcodeproj`。
2. 在 Xcode 左侧选 `PowerLedger` target → **Signing & Capabilities**：
   - 选择你的 Team；
   - 如果 `com.powercalc.ledger` 已被占用，把 Bundle Identifier 改成自己的（例如 `com.yourname.powercalc`）。
3. 选择 iPhone 模拟器或真机，按 `⌘R`。
4. 上 TestFlight / App Store：`Product → Archive`，在 Organizer 里 `Distribute App`。

也可以在工程目录执行：

```bash
# 模拟器 Debug 构建
xcodebuild \
  -project PowerLedger.xcodeproj \
  -scheme PowerLedger \
  -configuration Debug \
  -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  build

# 真机归档（需要先在 Xcode 里配置 Team 和签名）
xcodebuild \
  -project PowerLedger.xcodeproj \
  -scheme PowerLedger \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  -archivePath build/PowerLedger.xcarchive \
  archive
```

## 工程信息

- App 名称：功耗计算器
- Bundle ID：`com.powercalc.ledger`
- 版本：2.1.2（Build 13）
- 最低系统：iOS 15.0
- 设备：iPhone 竖屏
- 依赖：无（纯系统 SwiftUI / WebKit）
- 网络：无网络请求、无网络权限
- 状态持久化：WKWebView JavaScript 桥接 → `UserDefaults`
- 历史记录：按自然日保存在本机，保留 730 天（约 2 年）
- 每日归零：每天首次打开或跨天后回到前台，会把昨日用量归档，并清零今日步数、充电次数、电器时长和出行；身体资料、已勾选项目和固定项保留
- 配置保护：设置里的「锁定设备和电器电池容量、功率」只冻结电池容量、主机功率和电器功率；充电次数、使用时长和出行仍可录入

## 目录

```text
PowerLedger.xcodeproj/          可直接打开的 Xcode 工程和共享 Scheme
PowerLedger/
  PowerLedgerApp.swift          @main SwiftUI App
  PowerLedgerWebView.swift      WKWebView 壳、导航拦截、localStorage 桥接
  Info.plist                    竖屏、浅色状态栏、启动页、版本
  PrivacyInfo.xcprivacy         UserDefaults 隐私清单
  Assets.xcassets/              AppIcon / AccentColor / LaunchBackground
  Resources/web/                离线 HTML / CSS / JS（与 Android 同源）
.github/workflows/build-unsigned-ipa.yml  GitHub Actions 云端构建未签名 IPA
WINDOWS-SIDELOAD.md             Windows + Sideloadly 自签安装说明
sync-web-assets.sh              从 ../app/assets 同步最新页面
build-ios.sh                    简便构建脚本
```

## 从 Android 网页层同步更新

iOS 和 Android 共用同一套 `app/assets`。Android 页面更新后，在 Mac 或当前工程根目录运行：

```bash
./sync-web-assets.sh
```

再在 Xcode 里重新构建即可。资源文件夹 `Resources/web` 是 folder reference，会整体打包进 App。

## 实现说明

- `WKWebView` 只允许加载 App 包内 `Resources/web` 下的文件；其他 URL 一律取消。
- 页面通过 `loadFileURL(_:allowingReadAccessTo:)` 加载，完全离线。
- WKWebView 的 file origin 不方便依赖持久化，因此用 `WKUserScript` 在文档开始时注入本地存储 shim，写入通过 `WKScriptMessageHandler` 落到 `UserDefaults`：
  - `powercalc.state.v2` 保存当前设置；
  - `powercalc.history.v1` 保存 730 天历史；
  - `powercalc.profile.v1` 保存首次录入的年龄、身高、体重；
  - `powercalc.itemLocks.v1` 保存每张子卡片的固定状态。
- `PrivacyInfo.xcprivacy` 声明了 UserDefaults 访问原因 `CA92.1`；无追踪、无数据收集。
- App 图标使用 1024 全幅浅色图标；启动页为 `LaunchBackground` 奶油色。

## 验证范围

- Xcode 工程文件已用独立的 `pbxproj` 解析器检查：target、构建阶段、资源引用、Bundle ID、版本号、签名配置均可读。
- Info.plist / PrivacyInfo.xcprivacy XML 已解析校验；AppIcon / 颜色资源 JSON 已检查。
- Swift 源码和真机运行**未在本机编译验证**（没有 Xcode）。首次在 Mac 上构建时请先选择 Team，然后再运行。
- Web 界面已在 390×844 和 360×800 视口验证，包括首次身体资料、单卡三态固定、周边五档评价、特斯拉续航换算、历史记录和设备/电器/出行全部功能。
- 本工程仍未在本机编译或签名；在 Xcode 中首次构建时请先选择 Team。云端 workflow 只构建未签名 IPA，安装时由 Sideloadly 用你的 Apple ID 重签。
