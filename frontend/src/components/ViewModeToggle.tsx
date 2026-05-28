import type { ViewMode } from "../types/event";

interface Props {
  view: ViewMode;
  onChange: (v: ViewMode) => void;
}

export function ViewModeToggle({ view, onChange }: Props) {
  return (
    <div className="view-toggle">
      <button
        type="button"
        className={view === "public" ? "active" : ""}
        onClick={() => onChange("public")}
      >
        公共视角
      </button>
      <button
        type="button"
        className={view === "god" ? "active" : ""}
        onClick={() => onChange("god")}
      >
        上帝视角
      </button>
    </div>
  );
}
