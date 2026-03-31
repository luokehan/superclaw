<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import {
    adminScoreApi,
    type AdminScoreSummary,
    type AdminScoreLeaderboardItem,
    type AdminScoreLogItem,
    type AdminPageResponse,
} from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import {
    Search,
    RefreshCw,
    Loader2,
    AlertCircle,
    Trophy,
    TrendingUp,
    TrendingDown,
    Minus,
    ArrowLeft,
    ArrowRight,
    Users,
} from 'lucide-vue-next'

// ─── Tab ───

type TabType = 'leaderboard' | 'logs'
const activeTab = ref<TabType>('leaderboard')

// ─── 状态 ───

const PAGE_SIZE = 20

const loading = ref(false)
const summaryLoading = ref(false)
const error = ref('')

const keyword = ref('')
const roleFilter = ref('all')
const signFilter = ref('all') // for logs: all, positive, negative
const page = ref(1)
let requestId = 0

const summary = ref<AdminScoreSummary | null>(null)
const leaderboardData = ref<AdminPageResponse<AdminScoreLeaderboardItem>>(createEmptyPage())
const logsData = ref<AdminPageResponse<AdminScoreLogItem>>(createEmptyPage())

// ─── 选项 ───

const roleOptions = [
    { value: 'all', label: '全部角色' },
    { value: 'planner', label: '规划者' },
    { value: 'executor', label: '执行者' },
    { value: 'reviewer', label: '审查者' },
    { value: 'patrol', label: '巡查者' },
]

const signOptions = [
    { value: 'all', label: '全部' },
    { value: 'positive', label: '奖励' },
    { value: 'negative', label: '惩罚' },
]

// ─── 工具函数 ───

function createEmptyPage<T = unknown>(): AdminPageResponse<T> {
    return { items: [] as T[], total: 0, page: 1, page_size: PAGE_SIZE, total_pages: 1, has_more: false }
}

function formatRole(role: string) {
    return ({ planner: '规划者', executor: '执行者', reviewer: '审查者', patrol: '巡查者' }[role] ?? role)
}

function getRoleBadgeClass(role: string) {
    return ({
        planner: 'border-violet-200 bg-violet-50 text-violet-700',
        executor: 'border-sky-200 bg-sky-50 text-sky-700',
        reviewer: 'border-amber-200 bg-amber-50 text-amber-700',
        patrol: 'border-teal-200 bg-teal-50 text-teal-700',
    }[role] ?? 'border-border bg-muted text-muted-foreground')
}

function formatDate(value: string | null) {
    if (!value) return '—'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return '—'
    return new Intl.DateTimeFormat('zh-CN', {
        month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
    }).format(date)
}

function rankEmoji(rank: number) {
    if (rank === 1) return '🥇'
    if (rank === 2) return '🥈'
    if (rank === 3) return '🥉'
    return `#${rank}`
}

// ─── 数据加载 ───

const reloadDebounced = useDebounceFn(() => {
    page.value = 1
    void loadData()
}, 280)

watch([keyword, roleFilter, signFilter], () => {
    loading.value = true
    reloadDebounced()
})

watch(activeTab, () => {
    keyword.value = ''
    roleFilter.value = 'all'
    signFilter.value = 'all'
    page.value = 1
    void loadData()
})

onMounted(() => {
    void loadSummary()
    void loadData()
})

async function loadSummary() {
    summaryLoading.value = true
    try {
        const response = await adminScoreApi.summary()
        summary.value = response.data
    } catch (e) {
        console.error('Failed to load score summary', e)
    } finally {
        summaryLoading.value = false
    }
}

async function loadData() {
    const rid = ++requestId
    loading.value = true
    error.value = ''

    try {
        if (activeTab.value === 'leaderboard') {
            const response = await adminScoreApi.leaderboard({
                page: page.value,
                page_size: PAGE_SIZE,
                keyword: keyword.value.trim() || undefined,
                role: roleFilter.value === 'all' ? undefined : roleFilter.value,
                sort_by: 'total_score',
                sort_order: 'desc',
            })
            if (rid !== requestId) return
            leaderboardData.value = response.data
        } else {
            const response = await adminScoreApi.logs({
                page: page.value,
                page_size: PAGE_SIZE,
                keyword: keyword.value.trim() || undefined,
                score_sign: signFilter.value === 'all' ? undefined : signFilter.value,
                sort_order: 'desc',
            })
            if (rid !== requestId) return
            logsData.value = response.data
        }
    } catch (e) {
        if (rid !== requestId) return
        console.error('Failed to load score data', e)
        error.value = '数据加载失败，请重试。'
    } finally {
        if (rid === requestId) loading.value = false
    }
}

function goToPage(p: number) {
    const data = activeTab.value === 'leaderboard' ? leaderboardData.value : logsData.value
    if (p < 1 || p > data.total_pages || p === page.value) return
    page.value = p
    void loadData()
}

function refreshAll() {
    void loadSummary()
    void loadData()
}

// 当前分页数据（供模板统一引用）
function currentPageData() {
    return activeTab.value === 'leaderboard' ? leaderboardData.value : logsData.value
}
</script>

<template>
    <div class="flex flex-col h-[calc(100vh-3.5rem)]">
        <!-- ─── 概览卡片 ─── -->
        <header class="shrink-0 border-b border-border/40 bg-background px-4 py-4 space-y-4">
            <!-- 概览统计 -->
            <div v-if="summary" class="grid grid-cols-2 sm:grid-cols-4 gap-3 animate-slide-up">
                <div class="rounded-xl border border-border/50 bg-muted/20 p-3 text-center">
                    <div class="text-2xl font-bold tabular-nums text-primary">{{ summary.top_score }}</div>
                    <div class="text-[11px] text-muted-foreground mt-0.5">最高积分</div>
                </div>
                <div class="rounded-xl border border-border/50 bg-muted/20 p-3 text-center">
                    <div class="text-2xl font-bold tabular-nums">{{ summary.average_score.toFixed(1) }}</div>
                    <div class="text-[11px] text-muted-foreground mt-0.5">平均积分</div>
                </div>
                <div class="rounded-xl border border-border/50 bg-muted/20 p-3 text-center">
                    <div class="flex justify-center gap-3 text-sm tabular-nums">
                        <span class="text-emerald-600 font-semibold">{{ summary.positive_score_agents }}</span>
                        <span class="text-muted-foreground">/</span>
                        <span class="text-slate-500 font-semibold">{{ summary.zero_score_agents }}</span>
                        <span class="text-muted-foreground">/</span>
                        <span class="text-rose-500 font-semibold">{{ summary.negative_score_agents }}</span>
                    </div>
                    <div class="text-[11px] text-muted-foreground mt-0.5">正分 / 零分 / 负分</div>
                </div>
                <div class="rounded-xl border border-border/50 bg-muted/20 p-3 text-center">
                    <div class="text-2xl font-bold tabular-nums">{{ summary.total_agents }}</div>
                    <div class="text-[11px] text-muted-foreground mt-0.5">Agent 总数</div>
                </div>
            </div>

            <!-- 搜索 + Tab 切换 + 筛选 -->
            <div class="space-y-2.5">
                <div class="flex items-center gap-3">
                    <!-- Tab 切换 -->
                    <div class="flex gap-1 rounded-lg bg-muted/40 p-0.5">
                        <Button size="sm" :variant="activeTab === 'leaderboard' ? 'default' : 'ghost'"
                            class="h-7 rounded-md px-3 text-xs" @click="activeTab = 'leaderboard'">
                            <Trophy class="h-3 w-3 mr-1" />
                            排行榜
                        </Button>
                        <Button size="sm" :variant="activeTab === 'logs' ? 'default' : 'ghost'"
                            class="h-7 rounded-md px-3 text-xs" @click="activeTab = 'logs'">
                            积分流水
                        </Button>
                    </div>

                    <Separator orientation="vertical" class="h-4" />

                    <div class="relative flex-1 max-w-sm">
                        <Search
                            class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                        <Input v-model="keyword" class="h-9 bg-muted/30 pl-10 text-sm"
                            :placeholder="activeTab === 'leaderboard' ? '搜索 Agent 名称…' : '搜索原因…'" />
                    </div>

                    <Badge variant="secondary" class="h-7 px-2.5 text-xs tabular-nums shrink-0">
                        {{ currentPageData().total }} 条
                    </Badge>

                    <Button variant="ghost" size="icon" class="h-8 w-8 shrink-0" :disabled="loading"
                        @click="refreshAll">
                        <RefreshCw class="h-3.5 w-3.5" :class="loading ? 'animate-spin' : ''" />
                    </Button>
                </div>

                <!-- 筛选行 -->
                <div class="flex items-center gap-1.5">
                    <template v-if="activeTab === 'leaderboard'">
                        <Button v-for="option in roleOptions" :key="option.value" size="sm"
                            :variant="roleFilter === option.value ? 'default' : 'ghost'"
                            class="h-7 rounded-full px-3 text-xs" @click="roleFilter = option.value">
                            {{ option.label }}
                        </Button>
                    </template>
                    <template v-else>
                        <Button v-for="option in signOptions" :key="option.value" size="sm"
                            :variant="signFilter === option.value ? 'default' : 'ghost'"
                            class="h-7 rounded-full px-3 text-xs" @click="signFilter = option.value">
                            {{ option.label }}
                        </Button>
                    </template>
                </div>
            </div>
        </header>

        <!-- ─── 主内容 ─── -->
        <div class="flex-1 min-h-0 overflow-y-auto">
            <!-- 错误 -->
            <div v-if="error" class="flex flex-col items-center justify-center py-16">
                <AlertCircle class="h-5 w-5 text-muted-foreground" />
                <p class="mt-2 text-sm">{{ error }}</p>
                <Button class="mt-3" size="sm" @click="loadData">重新加载</Button>
            </div>

            <!-- 加载中 -->
            <div v-else-if="loading" class="flex items-center justify-center py-16">
                <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
            </div>

            <!-- ═══ 排行榜 ═══ -->
            <template v-else-if="activeTab === 'leaderboard'">
                <div v-if="leaderboardData.items.length" class="divide-y divide-border/30">
                    <div v-for="(item, idx) in leaderboardData.items" :key="item.agent_id"
                        class="group flex items-center gap-4 px-5 py-3.5 hover:bg-muted/20 transition-all duration-200 animate-slide-up"
                        :class="{
                            'bg-gradient-to-r from-amber-50/80 to-transparent dark:from-amber-950/20': item.rank === 1,
                            'bg-gradient-to-r from-slate-100/80 to-transparent dark:from-slate-800/20': item.rank === 2,
                            'bg-gradient-to-r from-orange-50/60 to-transparent dark:from-orange-950/15': item.rank === 3,
                        }"
                        :style="{ animationDelay: `${idx * 30}ms` }">
                        <!-- 排名 -->
                        <div class="w-10 text-center shrink-0">
                            <span class="text-lg font-bold"
                                :class="item.rank <= 3 ? 'text-primary' : 'text-muted-foreground/50'">
                                {{ rankEmoji(item.rank) }}
                            </span>
                        </div>

                        <!-- 名称 + 角色 -->
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-1.5">
                                <span class="text-sm font-semibold truncate">{{ item.agent_name }}</span>
                                <Badge variant="outline" :class="getRoleBadgeClass(item.role)"
                                    class="text-[10px] px-1.5 shrink-0">
                                    {{ formatRole(item.role) }}
                                </Badge>
                            </div>
                            <div class="flex gap-3 mt-0.5 text-[11px] text-muted-foreground tabular-nums">
                                <span>奖励 <span class="text-emerald-600 font-medium">{{ item.reward_count
                                }}</span></span>
                                <span>惩罚 <span class="text-rose-500 font-medium">{{ item.penalty_count
                                }}</span></span>
                                <span>共 {{ item.total_records }} 条</span>
                                <span v-if="item.last_score_at">最近 {{ formatDate(item.last_score_at) }}</span>
                            </div>
                        </div>

                        <!-- 积分 -->
                        <div class="text-right shrink-0">
                            <div class="text-lg font-bold tabular-nums transition-transform duration-150 group-hover:scale-110 origin-right"
                                :class="item.total_score > 0 ? 'text-emerald-600' : item.total_score < 0 ? 'text-rose-500' : 'text-muted-foreground'">
                                {{ item.total_score > 0 ? '+' : '' }}{{ item.total_score }}
                            </div>
                            <div class="text-[10px] text-muted-foreground/60">积分</div>
                        </div>
                    </div>
                </div>
                <div v-else class="flex flex-col items-center justify-center py-16 text-muted-foreground/40">
                    <Users class="h-6 w-6 mb-2" />
                    <p class="text-sm">暂无排行数据</p>
                </div>
            </template>

            <!-- ═══ 积分流水 ═══ -->
            <template v-else>
                <div v-if="logsData.items.length" class="divide-y divide-border/30">
                    <div v-for="(log, idx) in logsData.items" :key="log.id"
                        class="flex items-center gap-3 px-5 py-3 hover:bg-muted/20 transition-colors animate-slide-up"
                        :style="{ animationDelay: `${idx * 30}ms` }">
                        <!-- 加减符号 -->
                        <div class="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
                            :class="log.score_delta > 0 ? 'bg-emerald-100' : log.score_delta < 0 ? 'bg-rose-100' : 'bg-muted'">
                            <TrendingUp v-if="log.score_delta > 0" class="h-4 w-4 text-emerald-600" />
                            <TrendingDown v-else-if="log.score_delta < 0" class="h-4 w-4 text-rose-500" />
                            <Minus v-else class="h-4 w-4 text-muted-foreground" />
                        </div>

                        <!-- 详情 -->
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-1.5">
                                <span class="text-sm font-medium">{{ log.agent_name }}</span>
                                <span class="text-xs text-muted-foreground truncate">{{ log.reason }}</span>
                            </div>
                            <div class="text-[11px] text-muted-foreground/60 mt-0.5 tabular-nums">
                                {{ formatDate(log.created_at) }}
                            </div>
                        </div>

                        <!-- 积分变动 -->
                        <div class="text-right shrink-0">
                            <span class="text-sm font-bold tabular-nums"
                                :class="log.score_delta > 0 ? 'text-emerald-600' : log.score_delta < 0 ? 'text-rose-500' : ''">
                                {{ log.score_delta > 0 ? '+' : '' }}{{ log.score_delta }}
                            </span>
                        </div>
                    </div>
                </div>
                <div v-else class="flex flex-col items-center justify-center py-16 text-muted-foreground/40">
                    <Trophy class="h-6 w-6 mb-2" />
                    <p class="text-sm">暂无积分流水</p>
                </div>
            </template>

            <!-- 分页 -->
            <div v-if="!loading && !error && currentPageData().total_pages > 1"
                class="flex items-center justify-center gap-2 py-3 border-t border-border/30 text-xs text-muted-foreground">
                <Button variant="ghost" size="icon" class="h-7 w-7" :disabled="currentPageData().page <= 1 || loading"
                    @click="goToPage(currentPageData().page - 1)">
                    <ArrowLeft class="h-3 w-3" />
                </Button>
                <span class="tabular-nums">{{ currentPageData().page }} / {{ currentPageData().total_pages }}</span>
                <Button variant="ghost" size="icon" class="h-7 w-7"
                    :disabled="currentPageData().page >= currentPageData().total_pages || loading"
                    @click="goToPage(currentPageData().page + 1)">
                    <ArrowRight class="h-3 w-3" />
                </Button>
            </div>
        </div>
    </div>
</template>

