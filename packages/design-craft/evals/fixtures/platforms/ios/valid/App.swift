import SwiftUI

struct ReviewView: View {
    var body: some View {
        NavigationStack {
            Button("Complete review") {}
                .font(.body)
                .foregroundStyle(.tint)
                .frame(minWidth: 44, minHeight: 44)
                .navigationTitle("Review")
        }
    }
}
