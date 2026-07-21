import type { ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";

interface TicketProps {
  header?: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function Ticket({ header, children, footer }: TicketProps) {
  return (
    <View style={styles.frame}>
      {header ? (
        <>
          <Text style={styles.header}>{header}</Text>
          <View style={styles.rule} />
        </>
      ) : null}
      <View>{children}</View>
      {footer ? <View style={styles.footer}>{footer}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  frame: {
    backgroundColor: "#fff9e8",
    borderWidth: 2,
    borderStyle: "dashed",
    borderColor: "#b8a34a",
    borderRadius: 6,
    padding: 22,
  },
  header: {
    textAlign: "center",
    fontWeight: "800",
    fontSize: 16,
    letterSpacing: 1,
    paddingBottom: 8,
    color: "#000",
  },
  rule: {
    borderBottomWidth: 2,
    borderBottomColor: "#000",
    marginBottom: 14,
  },
  footer: { marginTop: 28 },
});

