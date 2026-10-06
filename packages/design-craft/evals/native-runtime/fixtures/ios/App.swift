import UIKit

private enum RuntimeInteraction {
    static func handle(_ url: URL, statusLabel: UILabel? = nil) -> Bool {
        NSLog("DESIGN_CRAFT_RUNTIME_URL_RECEIVED:%@", url.absoluteString)
        recordEvent("url-received:\(url.absoluteString)")
        let pathTarget = url.path.trimmingCharacters(
            in: CharacterSet(charactersIn: "/")
        )
        guard url.scheme == "designcraft-evidence",
              url.host == "confirm" || pathTarget == "confirm" else {
            return false
        }
        let attempt = URLComponents(url: url, resolvingAgainstBaseURL: false)?
            .queryItems?
            .first(where: { $0.name == "attempt" })?
            .value ?? "missing-attempt"
        return confirm(statusLabel: statusLabel, attempt: attempt)
    }

    static func recordLaunch() {
        writePendingMarker()
        recordEvent("launched")
    }

    static func confirm(
        statusLabel: UILabel? = nil,
        attempt: String = "manual"
    ) -> Bool {
        guard let documents = documentsDirectory() else {
            return false
        }
        do {
            try "Runtime interaction confirmed attempt=\(attempt)\n".write(
                to: documents.appendingPathComponent("runtime-interaction.txt"),
                atomically: true,
                encoding: .utf8
            )
            recordEvent("interaction-confirmed:\(attempt)")
            statusLabel?.text = "Runtime interaction confirmed"
            NSLog("DESIGN_CRAFT_RUNTIME_INTERACTION_CONFIRMED:%@", attempt)
            return true
        } catch {
            recordEvent("interaction-failed:\(error)")
            NSLog("DESIGN_CRAFT_RUNTIME_INTERACTION_FAILED:%@", String(describing: error))
            return false
        }
    }

    private static func writePendingMarker() {
        guard let documents = documentsDirectory() else {
            return
        }
        do {
            try "Runtime interaction pending\n".write(
                to: documents.appendingPathComponent("runtime-interaction.txt"),
                atomically: true,
                encoding: .utf8
            )
        } catch {
            NSLog(
                "DESIGN_CRAFT_RUNTIME_PENDING_MARKER_FAILED:%@",
                String(describing: error)
            )
        }
    }

    private static func documentsDirectory() -> URL? {
        guard let documents = FileManager.default.urls(
            for: .documentDirectory,
            in: .userDomainMask
        ).first else {
            NSLog("DESIGN_CRAFT_RUNTIME_INTERACTION_FAILED:no-documents-directory")
            return nil
        }
        do {
            try FileManager.default.createDirectory(
                at: documents,
                withIntermediateDirectories: true
            )
            return documents
        } catch {
            NSLog(
                "DESIGN_CRAFT_RUNTIME_INTERACTION_FAILED:create-documents:%@",
                String(describing: error)
            )
            return nil
        }
    }

    private static func recordEvent(_ event: String) {
        guard let documents = documentsDirectory() else {
            return
        }
        let eventLog = documents.appendingPathComponent("runtime-events.txt")
        let existing = (try? String(contentsOf: eventLog, encoding: .utf8)) ?? ""
        do {
            try (existing + event + "\n").write(
                to: eventLog,
                atomically: true,
                encoding: .utf8
            )
        } catch {
            NSLog("DESIGN_CRAFT_RUNTIME_EVENT_LOG_FAILED:%@", String(describing: error))
        }
    }
}

@main
final class AppDelegate: UIResponder, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        configurationForConnecting connectingSceneSession: UISceneSession,
        options: UIScene.ConnectionOptions
    ) -> UISceneConfiguration {
        let configuration = UISceneConfiguration(
            name: "Default Configuration",
            sessionRole: connectingSceneSession.role
        )
        configuration.delegateClass = SceneDelegate.self
        return configuration
    }

    func application(
        _ application: UIApplication,
        open url: URL,
        options: [UIApplication.OpenURLOptionsKey: Any] = [:]
    ) -> Bool {
        RuntimeInteraction.handle(url)
    }
}

final class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?
    private weak var statusLabel: UILabel?

    func scene(
        _ scene: UIScene,
        willConnectTo session: UISceneSession,
        options connectionOptions: UIScene.ConnectionOptions
    ) {
        guard let windowScene = scene as? UIWindowScene else {
            return
        }

        let controller = UIViewController()
        controller.view.backgroundColor = .systemBackground

        let title = UILabel()
        title.text = "Native runtime evidence"
        title.font = .preferredFont(forTextStyle: .title1)
        title.adjustsFontForContentSizeCategory = true
        title.accessibilityIdentifier = "evidence-title"

        let status = UILabel()
        status.text = UIAccessibility.isReduceMotionEnabled
            ? "Reduced Motion enabled"
            : "Reduced Motion disabled"
        status.font = .preferredFont(forTextStyle: .body)
        status.adjustsFontForContentSizeCategory = true
        status.accessibilityIdentifier = "evidence-status"
        statusLabel = status

        let button = UIButton(type: .system)
        button.setTitle("Confirm runtime", for: .normal)
        button.titleLabel?.font = .preferredFont(forTextStyle: .headline)
        button.accessibilityIdentifier = "evidence-action"
        button.heightAnchor.constraint(greaterThanOrEqualToConstant: 44).isActive = true
        button.addAction(UIAction { [weak self] _ in
            _ = RuntimeInteraction.confirm(statusLabel: self?.statusLabel)
        }, for: .touchUpInside)

        let stack = UIStackView(arrangedSubviews: [title, status, button])
        stack.axis = .vertical
        stack.spacing = 20
        stack.translatesAutoresizingMaskIntoConstraints = false
        controller.view.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(
                equalTo: controller.view.safeAreaLayoutGuide.leadingAnchor,
                constant: 24
            ),
            stack.trailingAnchor.constraint(
                equalTo: controller.view.safeAreaLayoutGuide.trailingAnchor,
                constant: -24
            ),
            stack.centerYAnchor.constraint(equalTo: controller.view.centerYAnchor),
        ])

        let window = UIWindow(windowScene: windowScene)
        window.rootViewController = controller
        window.makeKeyAndVisible()
        self.window = window
        RuntimeInteraction.recordLaunch()
        NSLog("DESIGN_CRAFT_RUNTIME_LAUNCHED")

        if let url = connectionOptions.urlContexts.first?.url {
            _ = RuntimeInteraction.handle(url, statusLabel: statusLabel)
        }
    }

    func scene(_ scene: UIScene, openURLContexts urlContexts: Set<UIOpenURLContext>) {
        guard let url = urlContexts.first?.url else {
            return
        }
        _ = RuntimeInteraction.handle(url, statusLabel: statusLabel)
    }
}
