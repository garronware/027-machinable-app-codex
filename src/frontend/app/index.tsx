import * as DocumentPicker from "expo-document-picker";
import { useRouter } from "expo-router";
import { Alert, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { BigButton } from "../components/BigButton";

export default function HomeScreen() {
  const router = useRouter();

  async function pickPdf() {
    const result = await DocumentPicker.getDocumentAsync({
      type: "application/pdf",
      copyToCacheDirectory: true,
      multiple: false,
    });
    if (result.canceled) {
      return;
    }
    const asset = result.assets[0];
    if (!asset) {
      Alert.alert("No PDF selected", "Choose a digitally generated PDF drawing.");
      return;
    }
    router.push({
      pathname: "/loading",
      params: { uri: asset.uri, filename: asset.name },
    });
  }

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <View style={styles.container}>
        <View>
          <Text style={styles.title}>MACHINABLE</Text>
          <View style={styles.rule} />
        </View>
        <View>
          <BigButton
            label="CHOOSE PDF DRAWING"
            icon="📄"
            variant="primary"
            onPress={pickPdf}
          />
          <Text style={styles.scope}>
            MVP SUPPORTS DIGITALLY GENERATED PDF DRAWINGS
          </Text>
        </View>
        <Text style={styles.tagline}>
          VERIFY EVERY RESULT AGAINST THE ORIGINAL PRINT
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#f2ecd8" },
  container: { flex: 1, padding: 22, justifyContent: "space-between" },
  title: {
    textAlign: "center",
    fontSize: 22,
    fontWeight: "800",
    letterSpacing: 2,
    color: "#000",
  },
  rule: { borderBottomWidth: 2, borderBottomColor: "#000", marginTop: 8 },
  scope: {
    marginTop: 16,
    textAlign: "center",
    fontSize: 11,
    lineHeight: 16,
    color: "#555",
  },
  tagline: {
    textAlign: "center",
    fontSize: 11,
    letterSpacing: 1,
    color: "#666",
  },
});

