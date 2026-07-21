import { StyleSheet, Text, View } from "react-native";

interface TicketRowProps {
  label: string;
  value: string;
}

export function TicketRow({ label, value }: TicketRowProps) {
  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <Text selectable style={styles.value}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    borderBottomWidth: 1,
    borderBottomColor: "#d7cfb5",
    paddingVertical: 10,
  },
  label: {
    color: "#68604c",
    fontSize: 10,
    letterSpacing: 0.7,
    textTransform: "uppercase",
  },
  value: { color: "#000", fontSize: 15, fontWeight: "600", marginTop: 3 },
});

