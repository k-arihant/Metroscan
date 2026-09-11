import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MoreHorizontal, ShieldAlert, Sparkles, CheckCircle2 } from "lucide-react";

export const MinimalCarousel = ({
  cards = [],
  title = "Statutory Compliance Breakdown",
  onCardClick,
}) => {
  const [activeId, setActiveId] = useState(cards[0]?.id || null);

  const activeCard = cards.find((c) => c.id === activeId);
  const secondaryCards = cards.filter((c) => c.id !== activeId);

  const handleBackgroundClick = (e) => {
    if (e.target === e.currentTarget) setActiveId(null);
  };

  return (
    <div className="w-full flex items-center justify-center bg-transparent py-4">
      <div
        className="w-full flex flex-col items-center justify-center select-none font-sans"
        onClick={handleBackgroundClick}
      >
        {/* Container */}
        <div className="w-full max-w-xl">
          <motion.div layout className="flex flex-col gap-3">
            {/* Expanded Card */}
            <AnimatePresence mode="popLayout">
              {activeCard && (
                <motion.div
                  key={activeCard.id}
                  layoutId={activeCard.id}
                  className={`relative flex w-full flex-col justify-between rounded-3xl p-6 text-white shadow-2xl ${activeCard.color} min-h-[190px] border border-white/20`}
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/20 backdrop-blur-md shadow-inner shrink-0">
                      {activeCard.icon ? (
                        <activeCard.icon size={26} className="text-white" />
                      ) : (
                        <Sparkles size={26} className="text-white" />
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1 text-xs font-bold px-3 py-1 rounded-full bg-white/20 backdrop-blur-md">
                        <CheckCircle2 size={12} />
                        {activeCard.badge || "Verified Rule"}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-end justify-between mt-4">
                    <div className="overflow-hidden mr-2">
                      <div className="text-xs font-mono font-bold uppercase tracking-wider opacity-75">
                        {activeCard.subtitle || "Statutory Check"}
                      </div>
                      <h3 className="text-xl sm:text-2xl font-black opacity-95 leading-tight truncate">
                        {activeCard.title}
                      </h3>
                      <p className="text-base sm:text-lg font-bold tracking-tight opacity-80 truncate mt-0.5">
                        {activeCard.value}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onCardClick?.(activeCard);
                      }}
                      className="rounded-full bg-white/25 px-4 py-2 text-xs font-black uppercase tracking-wider backdrop-blur-md hover:bg-white/40 transition-colors shrink-0 shadow"
                    >
                      Inspect
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Grid Layout of Compact Cards */}
            <motion.div
              layout
              className={`grid gap-3 transition-all duration-500 ${
                activeId ? "grid-cols-2 sm:grid-cols-3" : "grid-cols-2 sm:grid-cols-4"
              }`}
            >
              {(activeId ? secondaryCards : cards).map((card) => {
                const Icon = card.icon || Sparkles;
                return (
                  <motion.div
                    key={card.id}
                    layoutId={card.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveId(card.id);
                    }}
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                    className={`relative flex flex-col justify-between cursor-pointer rounded-2xl p-4 text-white shadow-lg border border-white/10 ${card.color} ${
                      activeId ? "h-28" : "h-32"
                    } hover:scale-[1.03] transition-transform`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="w-8 h-8 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center">
                        <Icon size={18} />
                      </div>
                      <div className="rounded-full bg-white/10 p-1">
                        <MoreHorizontal size={14} />
                      </div>
                    </div>

                    <div className="mt-1 overflow-hidden">
                      <h4 className="text-xs sm:text-sm font-bold opacity-90 truncate leading-tight">
                        {card.title}
                      </h4>
                      <p className="text-xs font-semibold text-white/70 truncate mt-0.5">
                        {card.value}
                      </p>
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};
