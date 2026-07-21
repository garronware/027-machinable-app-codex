import { useLocalSearchParams, useRouter } from "expo-router";
import { useMemo } from "react";
import { ScrollView, StyleSheet, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { BigButton } from "../components/BigButton";
import { Ticket } from "../components/Ticket";
import { TicketRow } from "../components/TicketRow";
import type { FinalOutput } from "../types/api";

function parseData(encoded: string | string[] | undefined): FinalOutput | null {
  if (!encoded) {
    return null;
  }
  const raw = Array.isArray(encoded) ? encoded[0] : encoded;
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(decodeURIComponent(raw)) as FinalOutput;
  } catch {
    return null;
  }
}

export default function ResultScreen() {
  const { data } = useLocalSearchParams<{ data: string }>();
  const router = useRouter();
  const result = useMemo(() => parseData(data), [data]);

  if (!result) {
    return (
      <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
        <ScrollView contentContainerStyle={styles.scroll}>
          <Ticket header="RESULT UNREADABLE">
            <Text>Unable to parse the backend result.</Text>
          </Ticket>
        </ScrollView>
      </SafeAreaView>
    );
  }

  const basics = result.Part_Basics;
  const material = result.Raw_Matl_Needed;
  const isRound = material.Stock_Shape.toUpperCase() === "ROUND";
  const warnings = result._analysis?.warnings ?? [];

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Ticket
          header="RAW STOCK ORDER"
          footer={
            <BigButton
              label="CHECK ANOTHER PDF"
              onPress={() => router.replace("/")}
            />
          }
        >
          <TicketRow label="Part Name" value={basics.Part_Name || "—"} />
          <TicketRow label="Part No" value={basics.Part_No || "—"} />
          <TicketRow label="Material" value={material.Matl_Name} />
          <TicketRow
            label="Form"
            value={`${material.Stock_Shape} ${material.Stock_Form}`}
          />
          {isRound ? (
            <TicketRow label="Stock Dia" value={material.Stock_Dia ?? "—"} />
          ) : (
            <>
              <TicketRow label="Stock Thk" value={material.Stock_Thk ?? "—"} />
              <TicketRow label="Stock W" value={material.Stock_W ?? "—"} />
            </>
          )}
          <TicketRow label="Cut Length" value={material.Cut_L} />
          <TicketRow
            label="Closest Drop"
            value={material.Closest_Drop_L}
          />
          <TicketRow
            label="12-Ft Bar Yields"
            value={material["12-Ft_Bar_Yields"]}
          />
          {warnings.length ? (
            <Text style={styles.warnings}>
              {warnings.map((warning) => `• ${warning}`).join("\n")}
            </Text>
          ) : null}
          <Text style={styles.verify}>
            VERIFY EVERY DIMENSION, MATERIAL, AND STOCK SIZE AGAINST THE
            ORIGINAL DRAWING BEFORE ORDERING OR CUTTING.
          </Text>
        </Ticket>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#f2ecd8" },
  scroll: { flexGrow: 1, padding: 22, justifyContent: "center" },
  warnings: {
    marginTop: 18,
    color: "#7a4d00",
    fontSize: 12,
    lineHeight: 18,
  },
  verify: {
    marginTop: 22,
    borderTopWidth: 2,
    borderTopColor: "#000",
    paddingTop: 14,
    fontSize: 11,
    lineHeight: 16,
    fontWeight: "800",
  },
});
