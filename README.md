# RikkaHub DeepSeek V4 patch pack

用途：在 RikkaHub 2.1.9 / Apr 20 release 源码上补 DeepSeek V4 Flash/Pro 的工具调用与思考模式支持，并用 GitHub Actions 构建 debug APK。

## 改了什么

1. `ai/src/main/java/me/rerere/ai/registry/ModelRegistry.kt`
   - 新增 `DEEPSEEK_V4_FLASH`
   - 新增 `DEEPSEEK_V4_PRO`
   - 两个模型都标记 `toolReasoningAbility()`

2. `ai/src/main/java/me/rerere/ai/provider/providers/openai/ChatCompletionsAPI.kt`
   - 对 `api.deepseek.com` 加 `thinking` 参数：
     - `{"thinking":{"type":"enabled"}}`
     - `{"thinking":{"type":"disabled"}}`
   - reasoning 开启且不是 AUTO 时传 `reasoning_effort`
   - 构建历史消息时保留 assistant 的 `reasoning_content`，避免 DeepSeek thinking + tool calls 后续轮次 400

## 用法

把这两个东西复制进你的 RikkaHub fork：

```text
scripts/patch_deepseek_v4.py
.github/workflows/build-rikkahub-deepseek-v4.yml
```

本地手动打补丁：

```bash
python3 scripts/patch_deepseek_v4.py
```

GitHub Actions：

1. Fork `rikkahub/rikkahub`
2. 把本包里的两个文件提交进去
3. 打开 GitHub -> Actions -> `Build RikkaHub DeepSeek V4 APK` -> Run workflow
4. 构建完下载 artifact：`rikkahub-deepseek-v4-debug-apks`

## google-services.json

workflow 默认会生成一个 dummy `app/google-services.json`，只为了让 debug APK 编译通过。

如果你自己有 Firebase 配置，可以在仓库 Secrets 里加：

```text
GOOGLE_SERVICES_JSON
```

值就是完整的 `google-services.json` 内容。

## 安装注意

这个 workflow 构建的是 debug 包，包名通常是：

```text
me.rerere.rikkahub.debug
```

它可以和官方 release 共存，但数据不互通。

如果你要构建同包名 release，用自己的签名也不能直接覆盖官方 APK；Android 会因为签名不同拒绝更新，需要先卸载官方包。
