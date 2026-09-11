import React from "react";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

const InteractiveHoverButton = React.forwardRef(
  ({ text = "Button", className, children, ...props }, ref) => {
    const label = children || text;
    return (
      <button
        ref={ref}
        className={cn(
          "group relative inline-flex min-w-[130px] cursor-pointer items-center justify-center overflow-hidden rounded-full border border-gov-blue/30 dark:border-blue-400/40 bg-white/90 dark:bg-gray-900/90 px-5 py-2.5 text-center font-bold text-sm text-gov-blue dark:text-white shadow-sm transition-all duration-300 hover:shadow-lg active:scale-95",
          className
        )}
        {...props}
      >
        <span className="relative z-10 inline-flex items-center gap-2 translate-x-1 transition-all duration-300 group-hover:translate-x-12 group-hover:opacity-0">
          {label}
        </span>
        <div className="absolute inset-0 z-20 flex h-full w-full translate-x-12 items-center justify-center gap-2 font-bold text-white opacity-0 transition-all duration-300 group-hover:translate-x-0 group-hover:opacity-100">
          <span>{label}</span>
          <ArrowRight size={16} />
        </div>
        {/* Background expanding pill effect - hidden when idle so it never covers the text */}
        <div className="absolute inset-0 z-0 scale-0 opacity-0 rounded-full bg-gov-blue dark:bg-blue-600 transition-all duration-300 ease-out group-hover:scale-100 group-hover:opacity-100 group-hover:rounded-full"></div>
      </button>
    );
  }
);

InteractiveHoverButton.displayName = "InteractiveHoverButton";

export { InteractiveHoverButton };
