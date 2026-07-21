import { Pressable, StyleSheet, Text } from "react-native";

interface BigButtonProps {
  label: string;
  icon?: string;
  variant?: "primary" | "secondary";
  onPress: () => void | Promise<void>;
}

export function BigButton({
  label,
  icon,
  variant = "primary",
  onPress,
}: BigButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        variant === "secondary" && styles.secondary,
        pressed && styles.pressed,
      ]}
    >
      <Text style={styles.label}>
        {icon ? `${icon}  ` : ""}
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 60,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f6c514",
    borderWidth: 2,
    borderColor: "#000",
    borderRadius: 5,
    paddingHorizontal: 16,
  },
  secondary: { backgroundColor: "#fff9e8" },
  pressed: { opacity: 0.7 },
  label: {
    color: "#000",
    fontSize: 15,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
});

