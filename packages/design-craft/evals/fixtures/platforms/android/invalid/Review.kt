package fixtures.android.invalid

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.clickable
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@Composable
fun BrokenReviewAction() {
    BackHandler(enabled = true) {}
    Text(
        text = "Complete review",
        color = Color(0xFF777777),
        fontSize = 12.dp,
        modifier = Modifier.size(32.dp).clickable {},
    )
}
