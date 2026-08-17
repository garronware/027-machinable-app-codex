export type StockFormIconKind = "flat-bar" | "plate" | "round-bar";

type StockFormIconProps = {
  form: StockFormIconKind;
};

function FlatBarIcon() {
  return (
    <svg viewBox="0 0 88 56" focusable="false" aria-hidden="true">
      <path className="stock-icon-top" d="m9 27 48-19 22 11-49 19Z" />
      <path className="stock-icon-side" d="m30 38 49-19v10L30 49Z" />
      <path className="stock-icon-end" d="M9 27 30 38v11L9 38Z" />
    </svg>
  );
}

function PlateIcon() {
  return (
    <svg viewBox="0 0 88 56" focusable="false" aria-hidden="true">
      <path className="stock-icon-top" d="m8 20 36-14 36 18-37 15Z" />
      <path className="stock-icon-side" d="m43 39 37-15v5L43 44Z" />
      <path className="stock-icon-end" d="M8 20 43 39v5L8 25Z" />
    </svg>
  );
}

function RoundBarIcon() {
  return (
    <svg viewBox="0 0 100 64" focusable="false" aria-hidden="true">
      <ellipse
        className="stock-icon-round-far"
        cx="76"
        cy="17"
        rx="10"
        ry="16"
        transform="rotate(-27 76 17)"
      />
      <path
        className="stock-icon-round-body-fill"
        d="M15.8 28.7 68.8 2.2 83.2 31.3 30.2 57.8Z"
      />
      <path
        className="stock-icon-round-edge"
        d="M15.8 28.7 68.8 2.2M30.2 57.8 83.2 31.3"
      />
      <ellipse
        className="stock-icon-round-front"
        cx="23"
        cy="43.5"
        rx="10"
        ry="16"
        transform="rotate(-27 23 43.5)"
      />
    </svg>
  );
}

export function StockFormIcon({ form }: StockFormIconProps) {
  if (form === "round-bar") return <RoundBarIcon />;
  if (form === "plate") return <PlateIcon />;
  return <FlatBarIcon />;
}
