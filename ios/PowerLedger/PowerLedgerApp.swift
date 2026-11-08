import SwiftUI

@main
struct PowerLedgerApp: App {
    var body: some Scene {
        WindowGroup {
            PowerLedgerWebView()
                .background(
                    Color(red: 247.0 / 255.0, green: 244.0 / 255.0, blue: 238.0 / 255.0)
                        .ignoresSafeArea()
                )
                .preferredColorScheme(.light)
        }
    }
}
