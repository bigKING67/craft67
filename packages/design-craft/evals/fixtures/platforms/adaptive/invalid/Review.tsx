import DeviceInfo from "react-native-device-info";
import { View } from "react-native";

export function BrokenReviewAction() {
  const phoneModel = DeviceInfo.getModel();
  return <View style={{ width: 390, height: phoneModel ? 844 : 852 }} />;
}
