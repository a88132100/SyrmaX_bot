export function QuickAction({ 
  href, 
  icon, 
  title, 
  desc 
}: {
  href: string
  icon: React.ReactNode
  title: string
  desc: string
}) {
  const handleClick = () => {
    window.location.href = href
  }

  return (
    <div 
      className="sx-card p-5 block hover:shadow-xl hover:brightness-105 transition cursor-pointer"
      onClick={handleClick}
    >
      <div className="flex items-start gap-4">
        <div className="p-3 rounded-xl bg-white/5">{icon}</div>
        <div>
          <div className="text-base font-medium">{title}</div>
          <div className="text-sm text-sx-subtext mt-0.5">{desc}</div>
        </div>
      </div>
    </div>
  )
}