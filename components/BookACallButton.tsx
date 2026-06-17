"use client";

import { useCallback } from "react";

// The Cal.com event link. Replace with the real Solvere event when ready.
// Set NEXT_PUBLIC_CALCOM_LINK at build time to override without editing code.
const CAL_LINK = process.env.NEXT_PUBLIC_CALCOM_LINK ?? "solvere/audit-call";

type Variant = "primary" | "nav";

const variantClasses: Record<Variant, string> = {
  // §7.2 primary CTA — 17px Inter 500, cream on teal, 14/28 padding, 8px radius.
  primary:
    "inline-flex items-center justify-center rounded-lg bg-teal px-[28px] py-[14px] text-[17px] font-medium leading-none text-cream transition-colors duration-200 ease-out hover:bg-teal-deep focus-visible:bg-teal-deep w-full sm:w-auto",
  // §7.1 nav CTA — 16px Inter 500, cream on teal, 10/20 padding, 6px radius.
  nav: "inline-flex items-center justify-center rounded-md bg-teal px-[20px] py-[10px] text-[16px] font-medium leading-none text-cream transition-colors duration-200 ease-out hover:bg-teal-deep focus-visible:bg-teal-deep",
};

// Lazy + module-singleton: Cal.com embed.js only loads on the first click,
// not on every page load. Avoids third-party cookies + script payload from
// dragging down LCP / Best-Practices.
let calApiPromise: Promise<unknown> | null = null;
async function ensureCalApi() {
  if (!calApiPromise) {
    calApiPromise = import("@calcom/embed-react").then(async ({ getCalApi }) => {
      const cal = await getCalApi();
      cal("ui", { hideEventTypeDetails: false, layout: "month_view" });
      return cal;
    });
  }
  return calApiPromise;
}

export function BookACallButton({
  label,
  variant = "primary",
  className = "",
  ariaLabel,
}: {
  label: string;
  variant?: Variant;
  className?: string;
  ariaLabel?: string;
}) {
  const onClick = useCallback(() => {
    void ensureCalApi();
  }, []);

  return (
    <button
      type="button"
      data-cal-link={CAL_LINK}
      data-cal-config='{"layout":"month_view"}'
      aria-label={ariaLabel ?? label}
      onClick={onClick}
      className={`${variantClasses[variant]} ${className}`.trim()}
    >
      {label}
    </button>
  );
}
