import { Pressable, Text, useWindowDimensions } from "react-native";

export function ReviewAction() {
  const { width } = useWindowDimensions();
  const compact = width < 600;
  return (
    <Pressable accessibilityRole="button" style={{ minHeight: 48 }}>
      <Text>{compact ? "Complete" : "Complete review"}</Text>
    </Pressable>
  );
}
