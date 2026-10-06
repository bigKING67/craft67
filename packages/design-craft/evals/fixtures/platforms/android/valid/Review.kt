package fixtures.android.valid

import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun ReviewAction() {
    Button(
        modifier = Modifier,
        onClick = {},
    ) {
        Text("Complete review", style = MaterialTheme.typography.labelLarge)
    }
}
