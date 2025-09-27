import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

export const sxButton = cva(
  "inline-flex items-center justify-center rounded-xl font-medium transition active:translate-y-[1px] disabled:opacity-50 disabled:cursor-not-allowed",
  {
    variants: {
      variant: {
        gold: "sx-gold hover:brightness-105",
        secondary: "bg-[#141A22] text-sx-text border border-white/10 hover:bg-[#161E28]",
        outline: "border border-gold-600/30 text-gold-400 hover:bg-gold-600/10",
        ghost: "text-sx-sub hover:text-sx-text hover:bg-white/5",
        danger: "bg-danger/15 text-danger border border-danger/30 hover:bg-danger/20",
      },
      size: { 
        lg: "h-12 px-5 gap-2", 
        md: "h-10 px-4 gap-2", 
        sm: "h-8 px-3 text-sm gap-1.5" 
      }
    }, 
    defaultVariants: { variant: "gold", size: "md" } 
  }
)

export type SxButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof sxButton> & {
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export function SxButton({ className, variant, size, leftIcon, rightIcon, children, ...props }: SxButtonProps) {
  return (
    <button className={cn(sxButton({ variant, size }), className)} {...props}>
      {leftIcon && <span className="mr-1.5">{leftIcon}</span>}
      {children}
      {rightIcon && <span className="ml-1.5">{rightIcon}</span>}
    </button>
  )
}