import SwiftUI

struct BrokenReviewView: View {
    var body: some View {
        Text("Review")
            .font(.system(size: 13))
            .foregroundStyle(Color(red: 0.3, green: 0.3, blue: 0.3))
            .navigationBarBackButtonHidden(true)
    }
}
