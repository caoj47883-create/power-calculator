import Foundation
import SwiftUI
import UIKit
import WebKit

/// Full-screen WKWebView shell for the offline Power Ledger interface.
/// The HTML/CSS/JS live in the app bundle under Resources/web.
struct PowerLedgerWebView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        configuration.defaultWebpagePreferences.allowsContentJavaScript = true
        configuration.defaultWebpagePreferences.preferredContentMode = .mobile
        configuration.preferences.javaScriptCanOpenWindowsAutomatically = false

        let controller = WKUserContentController()
        controller.add(context.coordinator, name: Coordinator.storageHandlerName)
        let savedValues: [String: String] = [
            "powercalc.state.v2": UserDefaults.standard.string(forKey: Coordinator.defaultsKey) ?? "",
            "powercalc.history.v1": UserDefaults.standard.string(forKey: Coordinator.historyDefaultsKey) ?? "",
            "powercalc.profile.v1": UserDefaults.standard.string(forKey: Coordinator.profileDefaultsKey) ?? "",
            "powercalc.itemLocks.v1": UserDefaults.standard.string(forKey: Coordinator.itemLocksDefaultsKey) ?? ""
        ]
        controller.addUserScript(
            WKUserScript(
                source: Self.storageBootstrapScript(savedValues: savedValues),
                injectionTime: .atDocumentStart,
                forMainFrameOnly: true
            )
        )
        configuration.userContentController = controller

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = context.coordinator
        webView.isOpaque = false
        webView.backgroundColor = .clear
        webView.scrollView.backgroundColor = .clear
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.scrollView.bounces = false
        webView.scrollView.showsVerticalScrollIndicator = false
        webView.scrollView.showsHorizontalScrollIndicator = false
        webView.scrollView.keyboardDismissMode = .interactive
        webView.allowsBackForwardNavigationGestures = false
        webView.allowsLinkPreview = false

        let webRoot = Bundle.main.resourceURL?.appendingPathComponent("web", isDirectory: true)
        context.coordinator.webRoot = webRoot

        if let webRoot = webRoot {
            let indexURL = webRoot.appendingPathComponent("index.html")
            if FileManager.default.fileExists(atPath: indexURL.path) {
                webView.loadFileURL(indexURL, allowingReadAccessTo: webRoot)
            } else {
                webView.loadHTMLString(Self.missingResourceHTML, baseURL: nil)
            }
        } else {
            webView.loadHTMLString(Self.missingResourceHTML, baseURL: nil)
        }

        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {
        // The page is fully event-driven; no SwiftUI state needs syncing back.
    }

    static let missingResourceHTML = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        html, body { height: 100%; margin: 0; }
        body {
          display: grid;
          place-items: center;
          background: #f7f4ee;
          color: #201c17;
          font-family: -apple-system, "PingFang SC", sans-serif;
          text-align: center;
        }
        h1 { font-size: 20px; margin: 0 0 8px; }
        p { color: #766d61; font-size: 13px; }
      </style>
    </head>
    <body>
      <div>
        <h1>页面资源缺失</h1>
        <p>请重新构建 App，让 Resources/web 一并打包。</p>
      </div>
    </body>
    </html>
    """

    /// A native-backed localStorage shim keeps the offline app's selected
    /// settings, one-time profile, per-card fixed state, and history in
    /// UserDefaults, independent of WKWebView file-origin storage.
    static func storageBootstrapScript(savedValues: [String: String]) -> String {
        let initialLiteral: String
        if let data = try? JSONSerialization.data(withJSONObject: savedValues),
           let encoded = String(data: data, encoding: .utf8) {
            initialLiteral = encoded
        } else {
            initialLiteral = "{}"
        }

        return """
        (function () {
          var INITIAL = \(initialLiteral);
          var memory = Object.create(null);
          for (var key in INITIAL) {
            if (Object.prototype.hasOwnProperty.call(INITIAL, key) &&
                typeof INITIAL[key] === 'string' &&
                INITIAL[key].length > 0) {
              memory[key] = INITIAL[key];
            }
          }

          function post(payload) {
            try {
              if (window.webkit &&
                  window.webkit.messageHandlers &&
                  window.webkit.messageHandlers.powerLedgerStorage) {
                window.webkit.messageHandlers.powerLedgerStorage.postMessage(payload);
              }
            } catch (error) {}
          }

          var storage = {
            getItem: function (key) {
              var normalized = String(key);
              return Object.prototype.hasOwnProperty.call(memory, normalized) ? memory[normalized] : null;
            },
            setItem: function (key, value) {
              var normalized = String(key);
              var normalizedValue = String(value);
              memory[normalized] = normalizedValue;
              post({ key: normalized, value: normalizedValue });
            },
            removeItem: function (key) {
              var normalized = String(key);
              delete memory[normalized];
              post({ key: normalized, remove: true });
            },
            clear: function () {
              memory = Object.create(null);
              post({ clear: true });
            },
            key: function (index) {
              var keys = Object.keys(memory);
              return index >= 0 && index < keys.length ? keys[index] : null;
            }
          };

          Object.defineProperty(storage, 'length', {
            get: function () { return Object.keys(memory).length; }
          });

          var installed = false;
          try {
            Object.defineProperty(window, 'localStorage', {
              value: storage,
              configurable: false
            });
            installed = true;
          } catch (error) {}

          // Some WebKit versions expose localStorage as a non-configurable
          // host object. In that case override the Storage prototype methods.
          if (!installed) {
            try {
              var proto = window.Storage && window.Storage.prototype;
              if (proto) {
                proto.getItem = storage.getItem;
                proto.setItem = storage.setItem;
                proto.removeItem = storage.removeItem;
                proto.clear = storage.clear;
                proto.key = storage.key;
                Object.defineProperty(proto, 'length', {
                  get: function () { return Object.keys(memory).length; }
                });
                installed = true;
              }
            } catch (error) {}
          }

          if (!installed) {
            try { window.localStorage = storage; } catch (ignored) {}
          }
        })();
        """
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
        static let storageHandlerName = "powerLedgerStorage"
        static let defaultsKey = "powerLedger.state.v2"
        static let historyDefaultsKey = "powerLedger.history.v1"
        static let profileDefaultsKey = "powerLedger.profile.v1"
        static let itemLocksDefaultsKey = "powerLedger.itemLocks.v1"
        static let userDefaultsKeys: [String: String] = [
            "powercalc.state.v2": "powerLedger.state.v2",
            "powercalc.history.v1": "powerLedger.history.v1",
            "powercalc.profile.v1": "powerLedger.profile.v1",
            "powercalc.itemLocks.v1": "powerLedger.itemLocks.v1"
        ]

        var webRoot: URL?

        func webView(
            _ webView: WKWebView,
            decidePolicyFor navigationAction: WKNavigationAction,
            decisionHandler: @escaping (WKNavigationActionPolicy) -> Void
        ) {
            guard let url = navigationAction.request.url else {
                decisionHandler(.cancel)
                return
            }

            // Never leave the bundled offline app, even if a future link
            // accidentally points at the network.
            if url.isFileURL, let webRoot = webRoot {
                let rootPath = webRoot.standardizedFileURL.path
                let targetPath = url.standardizedFileURL.path
                if targetPath.hasPrefix(rootPath) {
                    decisionHandler(.allow)
                    return
                }
            }

            decisionHandler(.cancel)
        }

        func userContentController(
            _ userContentController: WKUserContentController,
            didReceive message: WKScriptMessage
        ) {
            guard message.name == Coordinator.storageHandlerName,
                  let body = message.body as? [String: Any] else {
                return
            }

            if let shouldClear = body["clear"] as? Bool, shouldClear {
                for (_, defaultsKey) in Coordinator.userDefaultsKeys {
                    UserDefaults.standard.removeObject(forKey: defaultsKey)
                }
                return
            }

            guard let key = body["key"] as? String,
                  let defaultsKey = Coordinator.userDefaultsKeys[key] else {
                return
            }

            if let shouldRemove = body["remove"] as? Bool, shouldRemove {
                UserDefaults.standard.removeObject(forKey: defaultsKey)
                return
            }

            guard let value = body["value"] as? String,
                  value.utf8.count <= 512_000 else {
                return
            }

            UserDefaults.standard.set(value, forKey: defaultsKey)
        }
    }
}
