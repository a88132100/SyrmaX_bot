import { useNavigate, useLocation } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { SxButton } from '@/components/ui/sx-button'

export function BackBar({ fallback = "/dashboard" }: { fallback?: string }) {
  const navigate = useNavigate()
  const location = useLocation()

  const handleBack = () => {
    // 避免跳到舊版 UI，優先返回 dashboard
    if (location.key !== "default" && window.history.length > 2) {
      navigate(-1)
    } else {
      navigate(fallback)
    }
  }

  return (
    <div className="mb-4">
      <SxButton 
        variant="outline" 
        size="sm" 
        leftIcon={<ArrowLeft size={16} />} 
        onClick={handleBack}
      >
        返回
      </SxButton>
    </div>
  )
}
