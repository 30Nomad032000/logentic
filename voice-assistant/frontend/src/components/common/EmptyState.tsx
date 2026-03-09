interface EmptyStateProps {
  message: string;
}

export function EmptyState({ message }: EmptyStateProps) {
  return (
    <div className="text-center py-12 px-6 text-[#8a8478] font-mono text-xs tracking-[0.03em] leading-relaxed">
      <div className="w-10 h-10 mx-auto mb-3.5 rounded-full bg-[#211f1d] border border-[rgba(255,200,120,0.06)] flex items-center justify-center text-lg text-[#8a8478]">
        ~
      </div>
      {message}
    </div>
  );
}
