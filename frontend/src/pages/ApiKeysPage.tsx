import React, { useState } from 'react'
import { 
  Plus, 
  Search, 
  TestTube, 
  Eye, 
  EyeOff, 
  Edit, 
  Trash2, 
  KeyRound,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { SxButton } from '@/components/ui/sx-button'
import { BackBar } from '@/components/ui/BackBar'

interface ApiKey {
  id: string
  exchange: string
  label: string
  permissions: string[]
  status: 'active' | 'inactive' | 'error'
  lastVerified: string
  riskLevel: 'low' | 'medium' | 'high'
}

const mockApiKeys: ApiKey[] = [
  {
    id: '1',
    exchange: 'Binance',
    label: '主要交易帳戶',
    permissions: ['讀取', '交易'],
    status: 'active',
    lastVerified: '2024-01-20 14:30',
    riskLevel: 'low'
  }
]

export function ApiKeysPage() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>(mockApiKeys)
  const [searchTerm, setSearchTerm] = useState('')
  const [showAddDialog, setShowAddDialog] = useState(false)

  const filteredKeys = apiKeys.filter(key =>
    key.exchange.toLowerCase().includes(searchTerm.toLowerCase()) ||
    key.label.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <BackBar />
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-sx-text">API 金鑰管理</h1>
          <p className="text-sx-sub">管理您的交易所 API 金鑰和權限</p>
        </div>
        <SxButton 
          variant="gold" 
          size="lg"
          leftIcon={<Plus className="h-5 w-5" />}
          onClick={() => setShowAddDialog(true)}
        >
          新增金鑰
        </SxButton>
      </div>

      {/* Toolbar */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="搜尋交易所或標籤..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
        <SxButton variant="outline" leftIcon={<TestTube className="h-4 w-4" />}>
          批次測試連線
        </SxButton>
      </div>

      {/* API Keys Table */}
      <div className="sx-card overflow-hidden">
        {filteredKeys.length === 0 ? (
          <div className="text-center py-12">
            <KeyRound className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">
              尚未新增任何 API 金鑰
            </h3>
            <p className="text-muted-foreground mb-6">
              開始新增您的第一個 API 金鑰來啟用交易功能
            </p>
            <SxButton 
              variant="primary"
              leftIcon={<Plus className="h-4 w-4" />}
              onClick={() => setShowAddDialog(true)}
            >
              新增金鑰
            </SxButton>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200">
                <tr>
                  <th className="text-left p-4 font-semibold text-foreground">交易所</th>
                  <th className="text-left p-4 font-semibold text-foreground">標籤</th>
                  <th className="text-left p-4 font-semibold text-foreground">權限</th>
                  <th className="text-left p-4 font-semibold text-foreground">狀態</th>
                  <th className="text-left p-4 font-semibold text-foreground">操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredKeys.map((key) => (
                  <tr key={key.id} className="border-b border-gray-200/50 hover:bg-accent/50">
                    <td className="p-4">
                      <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                          <KeyRound className="h-4 w-4 text-primary" />
                        </div>
                        <span className="font-medium text-foreground">{key.exchange}</span>
                      </div>
                    </td>
                    <td className="p-4 text-foreground">{key.label}</td>
                    <td className="p-4">
                      <div className="flex space-x-1">
                        {key.permissions.map((permission, index) => (
                          <span 
                            key={index}
                            className="px-2 py-1 text-xs bg-secondary text-secondary-foreground rounded-md"
                          >
                            {permission}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="h-4 w-4 text-success" />
                        <span className="capitalize text-foreground">{key.status}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center space-x-2">
                        <SxButton variant="ghost" size="sm" leftIcon={<TestTube className="h-4 w-4" />}>
                          測試
                        </SxButton>
                        <SxButton variant="ghost" size="sm" leftIcon={<Edit className="h-4 w-4" />}>
                          編輯
                        </SxButton>
                        <SxButton variant="danger" size="sm" leftIcon={<Trash2 className="h-4 w-4" />}>
                          刪除
                        </SxButton>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}