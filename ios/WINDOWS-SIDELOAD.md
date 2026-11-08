# Windows 上安装 iOS 版（无需 Mac）

这条路的原理是：

1. **GitHub Actions 的免费 macOS 机器**负责编译 Xcode 工程，产出未签名 IPA；
2. 你的 **Windows 电脑**用 Sideloadly 连接 iPhone / iPad，用免费 Apple ID 重签并安装；
3. 免费 Apple ID 的签名有效期是 **7 天**，到期后需要重新安装/重签。App 本身不联网，数据和 Android 一样只保存在本机。

> 这不是 App Store 安装，不会上架，也不需要 $99/年的 Apple Developer Program。
>
> 如果你需要长期稳定使用、TestFlight 分发或上架，还是需要付费 Apple Developer 账号和对应的签名方式。

## 一、准备 GitHub Actions 构建

1. 在 Windows 上解压 `功耗计算器-iOS-v2.1.2-Xcode.zip`（包含 `WINDOWS-SIDELOAD.md` 和 `.github/workflows`）。
2. 注册/登录 GitHub（免费），新建一个仓库。
3. 把解压后的全部文件上传到这个仓库，包括隐藏目录 `.github/workflows/build-unsigned-ipa.yml`。
   - 推荐用 GitHub Desktop：`File → Add local repository`，选择解压目录，然后 `Publish repository`。
   - 也可以在 GitHub 网页上传：如果网页上传没有带上 `.github` 隐藏目录，就在网页里 `Add file → Create new file`，文件名输入 `.github/workflows/build-unsigned-ipa.yml`，把本地这个文件的内容粘进去并提交。
4. 打开仓库的 **Actions** 标签：
   - 选择 **Build unsigned iOS IPA**；
   - 点 **Run workflow**；
   - 等 macOS runner 完成（通常几分钟）。
5. 进入这次运行，下载 **Artifacts → PowerLedger-unsigned-ipa**。解压后得到：
   - `PowerLedger-unsigned.ipa`
   - `PowerLedger-unsigned.ipa.sha256`

这一步不需要 Mac、不需要安装 Xcode，也不需要签名证书。

## 二、Windows 上安装到 iPhone / iPad

1. 安装苹果的 **Apple Devices**（Microsoft Store 里可搜到；旧系统用 iTunes）。
2. 从 [Sideloadly 官网](https://sideloadly.io/) 下载并安装 Sideloadly。
3. 用数据线连接 iPhone / iPad：
   - 手机上点「信任此电脑」；
   - 解锁设备。
4. 打开 Sideloadly：
   - IPA 选择刚才的 `PowerLedger-unsigned.ipa`；
   - 设备选择你的 iPhone / iPad；
   - Apple ID 填自己的 Apple ID；
   - 点 Start，按提示输入密码和双重认证验证码。
5. 安装完成后，在 iPhone / iPad 上：
   - **设置 → 通用 → VPN 与设备管理**，信任你的开发者证书；
   - iOS 16 及以上：**设置 → 隐私与安全性 → 开发者模式**，打开并重启设备。
6. 回到主屏幕打开「功耗计算器」。

## 三、注意事项

- **7 天有效期**：免费 Apple ID 签名 7 天后过期，重新用 Sideloadly 安装一次即可；想自动续签可以用 AltStore + AltServer。
- **3 个 App 限制**：免费 Apple ID 最多同时签 3 个 App。
- **Bundle ID 冲突**：如果 `com.powercalc.ledger` 已被别的签名占用，在 `PowerLedger.xcodeproj` 里把 `PRODUCT_BUNDLE_IDENTIFIER` 改成自己的唯一 ID，再重新跑一次 GitHub Actions。
- **构建失败**：先在 Actions 日志里搜 `error:`；如果 runner 的 Xcode 版本导致签名/目的地参数不兼容，重点看 `xcodebuild` 那一步的完整日志。
- **安全**：Sideloadly 是第三方工具，登录 Apple ID 前自行确认从其官网下载；不要把 Apple ID 密码发给任何人。
- 安装后的 App 仍然完全离线，不申请网络或存储权限。
