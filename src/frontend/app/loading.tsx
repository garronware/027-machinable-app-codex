import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useRef, useState } from "react";
import { Platform, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Ticket } from "../components/Ticket";
import { analyzeDrawing, ApiError } from "../services/api";

const MONO = Platform.select({ ios: "Courier New", default: "monospace" });
const STEPS = [
  "PDF UPLOADED",
  "READING DRAWING",
  "RECONCILING VIEWS",
  "CHECKING DIMENSIONS",
  "SELECTING STOCK",
];
const STEP_INTERVAL_MS = 6000;

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return `${error.message}${error.status ? ` (HTTP ${error.status})` : ""}`;
  }
  return error instanceof Error ? error.message : "UNKNOWN ERROR";
}

export default function LoadingScreen() {
  const { uri, filename } = useLocalSearchParams<{
    uri: string;
    filename: string;
  }>();
  const router = useRouter();
  const [stepIndex, setStepIndex] = useState(0);
  const stopTimer = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!uri || !filename) {
      router.replace({
        pathname: "/error",
        params: { msg: "NO PDF PROVIDED" },
      });
      return;
    }

    const interval = setInterval(() => {
      setStepIndex((index) =>
        index < STEPS.length - 1 ? index + 1 : index,
      );
    }, STEP_INTERVAL_MS);
    stopTimer.current = () => clearInterval(interval);

    analyzeDrawing(uri, filename)
      .then((result) => {
        stopTimer.current?.();
        router.replace({
          pathname: "/result",
          params: {
            data: encodeURIComponent(JSON.stringify(result)),
          },
        });
      })
      .catch((error: unknown) => {
        stopTimer.current?.();
        router.replace({
          pathname: "/error",
          params: { msg: errorMessage(error) },
        });
      });

    return () => stopTimer.current?.();
  }, [filename, router, uri]);

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <View style={styles.container}>
        <Ticket header="ANALYZING DRAWING">
          <Text style={styles.gear}>⚙</Text>
          {STEPS.map((label, index) => {
            const mark =
              index < stepIndex ? "✓" : index === stepIndex ? "…" : " ";
            return (
              <Text key={label} style={styles.step}>
                [{mark}] {label}
              </Text>
            );
          })}
        </Ticket>
        <Text style={styles.footerNote}>
          DENSE DRAWINGS MAY TAKE MORE THAN A MINUTE
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#f2ecd8" },
  container: { flex: 1, padding: 22, justifyContent: "space-between" },
  gear: { textAlign: "center", fontSize: 64, marginVertical: 10 },
  step: {
    fontFamily: MONO,
    fontSize: 14,
    lineHeight: 28,
    color: "#000",
  },
  footerNote: {
    textAlign: "center",
    fontSize: 11,
    letterSpacing: 1,
    color: "#666",
    marginBottom: 12,
  },
});

