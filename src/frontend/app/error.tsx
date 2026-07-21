import { useLocalSearchParams, useRouter } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { BigButton } from "../components/BigButton";
import { Ticket } from "../components/Ticket";

export default function ErrorScreen() {
  const { msg } = useLocalSearchParams<{ msg: string }>();
  const router = useRouter();
  const detail = Array.isArray(msg) ? msg[0] : msg;

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <View style={styles.container}>
        <Ticket
          header="NO SAFE RECOMMENDATION"
          footer={
            <BigButton
              label="CHOOSE ANOTHER PDF"
              onPress={() => router.replace("/")}
            />
          }
        >
          <Text style={styles.glyph}>✕</Text>
          <Text style={styles.line}>
            CHECK THE PDF AND REVIEW THE ORIGINAL DRAWING.
          </Text>
          {detail ? <Text style={styles.detail}>{detail}</Text> : null}
        </Ticket>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#f2ecd8" },
  container: { flex: 1, padding: 22, justifyContent: "center" },
  glyph: { textAlign: "center", fontSize: 64, color: "#a33" },
  line: {
    textAlign: "center",
    fontSize: 14,
    marginTop: 12,
    fontWeight: "600",
  },
  detail: {
    textAlign: "center",
    fontSize: 11,
    color: "#666",
    marginTop: 14,
  },
});

