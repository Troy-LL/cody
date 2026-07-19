"use client";

export const PARTY_EMOJIS = ["🦩", "🪩", "🎉", "🦖", "🍕", "👾", "🐙", "🌵", "🎳", "🧁", "🛸", "🐸"];

export function EmojiPicker({
  value,
  onChange,
  idPrefix,
}: {
  value: string;
  onChange: (emoji: string) => void;
  idPrefix: string;
}) {
  return (
    <div className="emoji-row" role="radiogroup" aria-label="Pick your emoji">
      {PARTY_EMOJIS.map((emoji) => (
        <button
          key={emoji}
          type="button"
          data-testid={`${idPrefix}-emoji-${emoji}`}
          className={`emoji-pick${emoji === value ? " selected" : ""}`}
          aria-checked={emoji === value}
          role="radio"
          onClick={() => onChange(emoji)}
        >
          {emoji}
        </button>
      ))}
    </div>
  );
}
