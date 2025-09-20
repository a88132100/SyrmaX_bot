import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "sx-gradient-primary text-white shadow-lg hover:shadow-xl hover:scale-105 active:scale-95",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border",
        outline: "border border-border bg-background hover:bg-accent hover:text-accent-foreground",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        success: "bg-success text-white hover:bg-success/90 shadow-md hover:shadow-lg",
        warning: "bg-warning text-white hover:bg-warning/90 shadow-md hover:shadow-lg",
        danger: "bg-danger text-white hover:bg-danger/90 shadow-md hover:shadow-lg",
        icon: "h-10 w-10 rounded-lg hover:bg-accent hover:text-accent-foreground",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-md hover:shadow-lg",
      },
      size: {
        lg: "h-12 px-6 text-base",
        md: "h-10 px-4 text-sm",
        sm: "h-8 px-3 text-xs",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
)

export interface SxButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  loading?: boolean
  loadingText?: string
}

const SxButton = React.forwardRef<HTMLButtonElement, SxButtonProps>(
  ({ 
    className, 
    variant, 
    size, 
    leftIcon, 
    rightIcon, 
    loading = false, 
    loadingText,
    children, 
    disabled,
    ...props 
  }, ref) => {
    const isDisabled = disabled || loading
    
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={isDisabled}
        {...props}
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            {loadingText || "載入中..."}
          </>
        ) : (
          <>
            {leftIcon && <span className="mr-2">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="ml-2">{rightIcon}</span>}
          </>
        )}
      </button>
    )
  }
)
SxButton.displayName = "SxButton"

export { SxButton, buttonVariants }
