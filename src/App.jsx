import { forwardRef, useEffect, useMemo, useRef, useState } from "react";
import {
  AnimatePresence,
  motion,
  useMotionValue,
  useReducedMotion,
  useSpring,
  useTransform,
} from "framer-motion";
import {
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  BriefcaseBusiness,
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleDot,
  Clock3,
  Command,
  CornerDownLeft,
  Ellipsis,
  ExternalLink,
  Eye,
  EyeOff,
  Focus,
  FolderOpen,
  Github,
  GripVertical,
  Home,
  Inbox,
  KeyRound,
  Layers3,
  LayoutGrid,
  Menu,
  MessageCircle,
  MoonStar,
  MoreHorizontal,
  Music2,
  PartyPopper,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  SquarePen,
  SunMedium,
  TimerReset,
  Utensils,
  Users,
  WandSparkles,
  X,
  Zap,
} from "lucide-react";

const dayData = [
  { id: "mon", weekday: "周一", date: "19", label: "MON", isoDate: "2026-10-19" },
  { id: "tue", weekday: "周二", date: "20", label: "TUE", isoDate: "2026-10-20" },
  { id: "wed", weekday: "周三", date: "21", label: "WED", isoDate: "2026-10-21" },
  { id: "thu", weekday: "周四", date: "22", label: "THU", isoDate: "2026-10-22" },
  { id: "fri", weekday: "周五", date: "23", label: "FRI", isoDate: "2026-10-23" },
];

const filters = [
  { id: "all", label: "全部" },
  { id: "work", label: "工作事务", tone: "mint" },
  { id: "leisure", label: "娱乐", tone: "orange" },
  { id: "personal", label: "个人日常", tone: "violet" },
];

const categoryMeta = {
  work: {
    label: "工作事务",
    hint: "会议、项目推进与工作产出",
    tone: "mint",
    icon: BriefcaseBusiness,
  },
  leisure: {
    label: "娱乐",
    hint: "外出、聚会或与朋友共处",
    tone: "orange",
    icon: PartyPopper,
  },
  personal: {
    label: "个人日常",
    hint: "起居、运动、记录与独处时间",
    tone: "violet",
    icon: SquarePen,
  },
};

const MUSIC_EVENT_ID = "daily-music";
const API_BASE = (import.meta.env.VITE_ORBIT_API_URL || "").replace(/\/$/, "");
const DEFAULT_SCHEDULE_DATE = "2026-10-21";

function durationLabel(minutes) {
  const total = Math.max(1, Number(minutes) || 0);
  const hours = Math.floor(total / 60);
  const remaining = total % 60;
  if (!hours) return `${remaining} MIN`;
  return remaining ? `${hours} HR ${remaining}` : `${hours} HR`;
}

function formatDeadline(value) {
  if (!value) return "";
  const [datePart, timePart = ""] = value.split("T");
  const [, month = "", day = ""] = datePart.split("-");
  return `${month}/${day} ${timePart.slice(0, 5)}`.trim();
}

function scheduleToEvent(schedule) {
  const category = categoryMeta[schedule.type];
  const day = dayData.find((item) => item.isoDate === schedule.date);
  if (!category || !day) return null;
  return {
    id: schedule.id,
    day: day.id,
    date: schedule.date,
    time: schedule.startTime,
    duration: durationLabel(schedule.durationMinutes),
    durationMinutes: schedule.durationMinutes,
    deadline: schedule.deadline || null,
    title: schedule.title,
    meta: schedule.description,
    type: schedule.type,
    tone: category.tone,
    icon: category.icon,
    featured: schedule.featured,
    status: schedule.status,
    source: schedule.source,
    sourceUrl: schedule.sourceUrl,
  };
}

function dayToIsoDate(dayId) {
  return dayData.find((item) => item.id === dayId)?.isoDate || DEFAULT_SCHEDULE_DATE;
}

async function orbitApi(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });
  const payload = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    throw new Error(payload?.error || `API 请求失败：${response.status}`);
  }
  return payload;
}

function musicEventFromPayload(payload) {
  const song = payload?.recommendation;
  if (!song) return null;
  return {
    id: MUSIC_EVENT_ID,
    day: "wed",
    time: "10:30",
    duration: "NOW PLAYING",
    title: song.title,
    meta: [song.artist, payload.playlist?.name].filter(Boolean).join(" · "),
    type: "personal",
    tone: "violet",
    icon: Music2,
    isMusic: true,
    musicId: song.id,
    musicFile: song.file,
  };
}

const navItems = [
  { icon: Home, label: "概览" },
  { icon: CalendarDays, label: "日程", active: true, badge: "14" },
  { icon: Inbox, label: "收件箱", badge: "3" },
  { icon: Focus, label: "专注空间" },
  { icon: LayoutGrid, label: "项目" },
];

const toneMap = {
  lime: {
    label: "青柠",
    accent: "#c9f26f",
    rgb: "201, 242, 111",
    deep: "#dfff96",
  },
  violet: {
    label: "紫罗兰",
    accent: "#a79aff",
    rgb: "167, 154, 255",
    deep: "#c1b8ff",
  },
  orange: {
    label: "珊瑚",
    accent: "#ff9b6a",
    rgb: "255, 155, 106",
    deep: "#ffbf9f",
  },
  mint: {
    label: "薄荷",
    accent: "#7ee7cb",
    rgb: "126, 231, 203",
    deep: "#a7f4df",
  },
};

const spring = { type: "spring", stiffness: 380, damping: 32 };

function OrbitMark({ compact = false }) {
  return (
    <div className={`brand-mark ${compact ? "is-compact" : ""}`}>
      <motion.span
        className="brand-orbit brand-orbit-a"
        animate={{ rotate: 360 }}
        transition={{ duration: 12, ease: "linear", repeat: Infinity }}
      />
      <motion.span
        className="brand-orbit brand-orbit-b"
        animate={{ rotate: -360 }}
        transition={{ duration: 9, ease: "linear", repeat: Infinity }}
      />
      <span className="brand-core" />
    </div>
  );
}

function Sidebar({ isOpen, setIsOpen, scheduleCount }) {
  return (
    <>
      <motion.aside
        className={`sidebar ${isOpen ? "mobile-open" : ""}`}
        initial={{ x: -24, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="brand-row">
          <OrbitMark />
          <span className="brand-word">ORBIT</span>
          <span className="brand-tag">BETA</span>
          <button
            className="icon-button sidebar-close"
            onClick={() => setIsOpen(false)}
            aria-label="关闭导航"
          >
            <X size={18} />
          </button>
        </div>

        <div className="workspace-switch">
          <div className="workspace-avatar">H</div>
          <div>
            <span className="eyebrow tiny">WORKSPACE</span>
            <strong>个人工作室</strong>
          </div>
          <ChevronRight size={15} />
        </div>

        <nav className="main-nav" aria-label="主导航">
          <p className="nav-label">你的空间</p>
          {navItems.map((item, index) => (
            <motion.button
              key={item.label}
              className={`nav-item ${item.active ? "active" : ""}`}
              initial={{ x: -12, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.08 + index * 0.055 }}
              whileHover={{ x: 4 }}
              onClick={() => setIsOpen(false)}
            >
              <item.icon size={18} strokeWidth={1.8} />
              <span>{item.label}</span>
              {item.badge && (
                <small>{item.label === "日程" ? scheduleCount : item.badge}</small>
              )}
              {item.active && (
                <motion.i
                  className="nav-active-glow"
                  layoutId="activeNav"
                  transition={spring}
                />
              )}
            </motion.button>
          ))}
        </nav>

        <div className="sidebar-calendar">
          <div className="mini-calendar-head">
            <span>10月 2026</span>
            <div>
              <button aria-label="上个月">
                <ChevronLeft size={13} />
              </button>
              <button aria-label="下个月">
                <ChevronRight size={13} />
              </button>
            </div>
          </div>
          <div className="calendar-grid weekdays">
            {["一", "二", "三", "四", "五", "六", "日"].map((day) => (
              <span key={day}>{day}</span>
            ))}
          </div>
          <div className="calendar-grid days">
            {Array.from({ length: 35 }, (_, index) => {
              const day = index - 2;
              const inMonth = day > 0 && day <= 31;
              const active = day === 21;
              const hasEvent = [7, 12, 16, 21, 22, 25, 28].includes(day);
              return (
                <button
                  key={index}
                  className={`${active ? "today" : ""} ${
                    !inMonth ? "muted" : ""
                  }`}
                >
                  {inMonth ? day : ""}
                  {hasEvent && <i />}
                </button>
              );
            })}
          </div>
        </div>

        <div className="sidebar-footer">
          <motion.div
            className="energy-card"
            whileHover={{ y: -2 }}
            transition={spring}
          >
            <div className="energy-top">
              <div className="energy-icon">
                <Zap size={16} fill="currentColor" />
              </div>
              <span>本周能量</span>
              <strong>78%</strong>
            </div>
            <div className="energy-track">
              <motion.span
                initial={{ width: 0 }}
                animate={{ width: "78%" }}
                transition={{ duration: 1.2, delay: 0.8, ease: "circOut" }}
              />
            </div>
            <p>比上周多 12%，节奏很好。</p>
          </motion.div>
          <button className="nav-item settings-item">
            <Settings2 size={18} />
            <span>设置</span>
            <Command size={14} />
          </button>
        </div>
      </motion.aside>
      <AnimatePresence>
        {isOpen && (
          <motion.button
            className="sidebar-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
            aria-label="关闭导航"
          />
        )}
      </AnimatePresence>
    </>
  );
}

function TiltCard({ children, className = "" }) {
  const rotateX = useSpring(0, { stiffness: 220, damping: 22 });
  const rotateY = useSpring(0, { stiffness: 220, damping: 22 });
  const reducedMotion = useReducedMotion();

  const handleMove = (event) => {
    if (reducedMotion) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const px = (event.clientX - rect.left) / rect.width;
    const py = (event.clientY - rect.top) / rect.height;
    rotateY.set((px - 0.5) * 5);
    rotateX.set((0.5 - py) * 5);
  };

  return (
    <motion.div
      className={className}
      style={{ rotateX, rotateY, transformPerspective: 900 }}
      onPointerMove={handleMove}
      onPointerLeave={() => {
        rotateX.set(0);
        rotateY.set(0);
      }}
    >
      {children}
    </motion.div>
  );
}

function Topbar({ onMenu }) {
  return (
    <motion.header
      className="topbar"
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <button className="icon-button mobile-menu" onClick={onMenu} aria-label="打开导航">
        <Menu size={20} />
      </button>
      <div className="topbar-date">
        <span className="status-dot" />
        <span>2026 年 10 月 21 日 · 星期三</span>
      </div>
      <div className="topbar-actions">
        <motion.button
          className="search-pill"
          whileHover={{ borderColor: "rgba(255,255,255,.22)" }}
          whileTap={{ scale: 0.98 }}
        >
          <Search size={16} />
          <span>搜索日程、任务...</span>
          <kbd>⌘ K</kbd>
        </motion.button>
        <button className="icon-button notification-button" aria-label="通知">
          <Bell size={18} />
          <span />
        </button>
        <div className="profile-pill">
          <div className="profile-avatar">
            <span>LY</span>
          </div>
          <div>
            <strong>Lynn</strong>
            <span>Product Designer</span>
          </div>
          <ChevronRight size={14} />
        </div>
      </div>
    </motion.header>
  );
}

function Greeting({ onAdd, eventCount }) {
  const container = {
    hidden: {},
    show: { transition: { staggerChildren: 0.08, delayChildren: 0.15 } },
  };
  const line = {
    hidden: { y: 32, opacity: 0 },
    show: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.75, ease: [0.22, 1, 0.36, 1] },
    },
  };

  return (
    <section className="hero">
      <motion.div variants={container} initial="hidden" animate="show">
        <motion.p className="eyebrow hero-eyebrow" variants={line}>
          <MoonStar size={13} /> WEDNESDAY, 21 OCT
        </motion.p>
        <motion.h1 variants={line}>
          让今天，<span>自然发生。</span>
        </motion.h1>
        <motion.p className="hero-subtitle" variants={line}>
          你有 <strong>{eventCount} 个日程</strong>，
          <span>最值得投入的 2 小时</span>在下午。
        </motion.p>
      </motion.div>

      <motion.div
        className="hero-actions"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.44 }}
      >
        <div className="weather-orb">
          <SunMedium size={20} />
        </div>
        <div className="weather-copy">
          <span>上海</span>
          <strong>25°</strong>
        </div>
        <motion.button
          className="primary-button"
          onClick={onAdd}
          whileHover={{ y: -2 }}
          whileTap={{ scale: 0.97 }}
          transition={spring}
        >
          <Plus size={17} />
          新建日程
        </motion.button>
      </motion.div>
    </section>
  );
}

function DayColumn({
  day,
  events,
  selectedId,
  setSelectedId,
  boardRef,
  dayRefs,
  onMove,
  onAdd,
  onToggleStatus,
  onMusicRefresh,
  musicStatus,
  dayIndex,
}) {
  const [isOver, setIsOver] = useState(false);
  const isToday = day.id === "wed";

  return (
    <motion.div
      className={`day-column ${isToday ? "today-column" : ""} ${
        isOver ? "is-over" : ""
      }`}
      ref={(node) => {
        dayRefs.current[day.id] = node;
      }}
      initial={{ opacity: 0, y: 22 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.26 + dayIndex * 0.06, duration: 0.5 }}
    >
      <div className="day-heading">
        <div>
          <span className="day-label">{day.label}</span>
          <strong className={isToday ? "today-number" : ""}>{day.date}</strong>
        </div>
        {isToday ? (
          <span className="today-chip">今天</span>
        ) : (
          <span className="day-count">{events.length}</span>
        )}
      </div>

      <div className="events-stack">
        {isToday && (
          <motion.div
            className="now-line"
            initial={{ scaleX: 0, opacity: 0 }}
            animate={{ scaleX: 1, opacity: 1 }}
            transition={{ delay: 1, duration: 0.7 }}
          >
            <span>10:24</span>
            <i />
          </motion.div>
        )}
        <AnimatePresence mode="popLayout">
          {events.map((event, index) => (
            <ScheduleCard
              key={event.id}
              event={event}
              index={index}
              selected={selectedId === event.id}
              setSelectedId={setSelectedId}
              boardRef={boardRef}
              dayRefs={dayRefs}
              onMove={(dayId) => onMove(event.id, dayId)}
              onToggleStatus={onToggleStatus}
              setIsOver={setIsOver}
              onMusicRefresh={onMusicRefresh}
              musicStatus={musicStatus}
            />
          ))}
        </AnimatePresence>
        {events.length === 0 && (
          <motion.div className="empty-day" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <span>空白也是安排。</span>
            <button onClick={() => onAdd(day.id)}>留给自己</button>
          </motion.div>
        )}
      </div>

      <motion.button
        className="day-add"
        onClick={() => onAdd(day.id)}
        whileHover={{ opacity: 1 }}
      >
        <Plus size={14} />
        添加
      </motion.button>
    </motion.div>
  );
}

const ScheduleCard = forwardRef(function ScheduleCard(
  {
    event,
    index,
    selected,
    setSelectedId,
    boardRef,
    dayRefs,
    onMove,
    onToggleStatus,
    setIsOver,
    onMusicRefresh,
    musicStatus,
  },
  forwardedRef,
) {
  const tone = toneMap[event.tone];
  const Icon = event.icon;
  const done = event.status === "done";
  const [dragging, setDragging] = useState(false);
  const reducedMotion = useReducedMotion();

  const handleDrag = (_, info) => {
    setIsOver(true);
    let hitDay = null;
    Object.entries(dayRefs.current).forEach(([id, node]) => {
      if (!node) return;
      const rect = node.getBoundingClientRect();
      if (info.point.x >= rect.left && info.point.x <= rect.right) hitDay = id;
    });
    setIsOver(Boolean(hitDay));
  };

  const handleDragEnd = (_, info) => {
    let hitDay = null;
    Object.entries(dayRefs.current).forEach(([id, node]) => {
      if (!node) return;
      const rect = node.getBoundingClientRect();
      if (info.point.x >= rect.left && info.point.x <= rect.right) hitDay = id;
    });
    if (hitDay && hitDay !== event.day) onMove(hitDay);
    setIsOver(false);
    setDragging(false);
  };

  return (
    <motion.article
      ref={forwardedRef}
      layout
      className={`schedule-card tone-${event.tone} ${
        event.featured ? "featured" : ""
      } ${selected ? "selected" : ""} ${done ? "is-done" : ""} ${
        event.isMusic ? "music-card-schedule" : ""
      }`}
      style={{ "--accent": tone.accent, "--accent-rgb": tone.rgb }}
      initial={{ opacity: 0, y: 18, scale: 0.96 }}
      animate={{ opacity: done ? 0.54 : 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9, x: 20 }}
      transition={{
        layout: spring,
        opacity: { duration: 0.2 },
        default: { delay: 0.48 + index * 0.055, duration: 0.42 },
      }}
      whileHover={done ? {} : { y: -4, scale: 1.012 }}
      whileTap={{ scale: 0.99 }}
      onClick={() => setSelectedId(event.id)}
      drag={!reducedMotion && !event.isMusic}
      dragConstraints={boardRef}
      dragElastic={0.12}
      dragMomentum={false}
      onDragStart={() => {
        setDragging(true);
        setSelectedId(event.id);
      }}
      onDrag={handleDrag}
      onDragEnd={handleDragEnd}
    >
      <div className="card-time-row">
        <span>{event.time}</span>
        <i />
        <span>{event.duration}</span>
        {event.source === "github" && (
          <a
            className="github-card-source"
            href={event.sourceUrl}
            target="_blank"
            rel="noreferrer"
            onClick={(clickEvent) => clickEvent.stopPropagation()}
            title="打开 GitHub 仓库"
          >
            <Github size={7} />
            REPO
          </a>
        )}
        {event.isMusic ? (
          <span className="music-source">本地歌单</span>
        ) : (
          <GripVertical className="drag-handle" size={14} />
        )}
      </div>
      <div className="card-main">
        <div className="event-icon">
          <Icon size={17} />
        </div>
        <div className="event-copy">
          <h3>{event.title}</h3>
          <p>{event.meta}</p>
        </div>
        {event.isMusic ? (
          <button
            className={`music-refresh ${
              musicStatus === "refreshing" ? "is-spinning" : ""
            }`}
            onClick={(clickEvent) => {
              clickEvent.stopPropagation();
              onMusicRefresh?.();
            }}
            disabled={musicStatus === "refreshing"}
            aria-label="随机换一首歌"
            title="随机换一首歌"
          >
            <RefreshCw size={12} />
          </button>
        ) : (
          <button
            className={`complete-toggle ${done ? "checked" : ""}`}
            onClick={(clickEvent) => {
              clickEvent.stopPropagation();
              onToggleStatus?.(event.id);
            }}
            aria-label={done ? "标记为未完成" : "标记为完成"}
          >
            <Check size={12} />
          </button>
        )}
      </div>
      {event.deadline && !event.isMusic && (
        <span className="card-deadline">
          <Clock3 size={8} />
          截止 {formatDeadline(event.deadline)}
        </span>
      )}
      {event.isMusic && (
        <span className="music-equalizer" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
      )}
      {event.featured && (
        <div className="card-sheen">
          <span />
        </div>
      )}
      <AnimatePresence>
        {dragging && (
          <motion.div
            className="drag-hint"
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            拖到任意一天
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
});

function Board({
  events,
  selectedId,
  setSelectedId,
  filter,
  setFilter,
  onMove,
  onAdd,
  onToggleStatus,
  scheduleStatus,
  onOpenGithub,
  onOpenMusic,
  onMusicRefresh,
  musicStatus,
  view,
  setView,
}) {
  const boardRef = useRef(null);
  const dayRefs = useRef({});
  const filteredEvents = useMemo(() => {
    const filtered =
      filter === "all" ? events : events.filter((event) => event.type === filter);
    return [...filtered].sort((a, b) => a.time.localeCompare(b.time));
  }, [events, filter]);

  return (
    <motion.section
      className="board-panel"
      initial={{ opacity: 0, y: 26 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.65, delay: 0.14 }}
    >
      <div className="board-toolbar">
        <div className="board-title">
          <div className="calendar-icon-wrap">
            <CalendarDays size={18} />
            <span>21</span>
          </div>
          <div>
            <span className="eyebrow tiny">SCHEDULE</span>
            <h2>本周节奏</h2>
          </div>
        </div>
        <div className="board-controls">
          <div className="filter-tabs">
            {filters.map((item) => (
              <button
                key={item.id}
                className={filter === item.id ? "active" : ""}
                onClick={() => setFilter(item.id)}
              >
                {item.tone && <i className={`filter-dot ${item.tone}`} />}
                {item.label}
                {filter === item.id && (
                  <motion.span
                    className="filter-bg"
                    layoutId="filterBg"
                    transition={spring}
                  />
                )}
              </button>
            ))}
          </div>
          <div className="view-switch">
            {["日", "周", "月"].map((item) => (
              <button
                key={item}
                className={view === item ? "active" : ""}
                onClick={() => setView(item)}
              >
                {item}
                {view === item && (
                  <motion.span
                    className="view-bg"
                    layoutId="viewBg"
                    transition={spring}
                  />
                )}
              </button>
            ))}
          </div>
          <button className="github-sync-button" onClick={onOpenGithub}>
            <Github size={13} />
            <span>GitHub</span>
          </button>
          <button
            className="github-sync-button music-library-button"
            onClick={onOpenMusic}
          >
            <FolderOpen size={13} />
            <span>音乐库</span>
          </button>
          <button className="icon-button board-more" aria-label="更多操作">
            <MoreHorizontal size={19} />
          </button>
        </div>
      </div>

      <div className="board-meta-row">
        <button className="week-nav">
          <ChevronLeft size={15} />
        </button>
        <span>10 月 19 日 — 10 月 23 日</span>
        <button className="week-nav">
          <ChevronRight size={15} />
        </button>
        <span className="week-badge">第 43 周</span>
        <span className={`storage-status ${scheduleStatus}`}>
          <CircleDot size={8} />
          {scheduleStatus === "ready"
            ? "本地已保存"
            : scheduleStatus === "offline"
              ? "存储未连接"
              : scheduleStatus === "saving"
                ? "保存中"
              : "读取中"}
        </span>
        <div className="board-tip">
          <GripVertical size={13} />
          拖动卡片调整日期
        </div>
      </div>

      <div className="week-board" ref={boardRef}>
        {view === "周" &&
          dayData.map((day, index) => (
            <DayColumn
              key={day.id}
              day={day}
              dayIndex={index}
              events={filteredEvents.filter((event) => event.day === day.id)}
              selectedId={selectedId}
              setSelectedId={setSelectedId}
              boardRef={boardRef}
              dayRefs={dayRefs}
              onMove={onMove}
              onAdd={onAdd}
              onToggleStatus={onToggleStatus}
              onMusicRefresh={onMusicRefresh}
              musicStatus={musicStatus}
            />
          ))}
        {view === "日" && (
          <DayFocusView
            events={filteredEvents.filter((event) => event.day === "wed")}
            selectedId={selectedId}
            setSelectedId={setSelectedId}
            onAdd={() => onAdd("wed")}
          />
        )}
        {view === "月" && (
          <MonthView
            events={filteredEvents}
            onAdd={onAdd}
            selectedId={selectedId}
            setSelectedId={setSelectedId}
          />
        )}
      </div>
    </motion.section>
  );
}

function DayFocusView({ events, selectedId, setSelectedId, onAdd }) {
  return (
    <motion.div
      className="day-focus-view"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
    >
      <div className="timeline-labels">
        {["08", "10", "12", "14", "16", "18", "20"].map((time) => (
          <span key={time}>{time}:00</span>
        ))}
      </div>
      <div className="focus-schedule">
        {events.map((event, index) => {
          const ToneIcon = event.icon;
          const tone = toneMap[event.tone];
          return (
            <motion.button
              key={event.id}
              className={`focus-event ${selectedId === event.id ? "selected" : ""}`}
              style={{
                "--accent": tone.accent,
                "--accent-rgb": tone.rgb,
                marginTop: index === 0 ? 16 : 0,
              }}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.08 }}
              onClick={() => setSelectedId(event.id)}
            >
              <span className="focus-time">{event.time}</span>
              <span className="focus-slot">
                <i>
                  <ToneIcon size={15} />
                </i>
                <span>
                  <strong>{event.title}</strong>
                  <small>{event.meta}</small>
                </span>
                <small>{event.duration}</small>
              </span>
            </motion.button>
          );
        })}
        <motion.button className="focus-add" onClick={onAdd} whileHover={{ scale: 1.01 }}>
          <Plus size={15} /> 插入一段新的专注
        </motion.button>
      </div>
    </motion.div>
  );
}

function MonthView({ events, onAdd, selectedId, setSelectedId }) {
  const weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
  const dayMap = { mon: 19, tue: 20, wed: 21, thu: 22, fri: 23 };
  return (
    <motion.div
      className="month-view"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
    >
      <div className="month-weekdays">
        {weekdays.map((day) => (
          <span key={day}>{day}</span>
        ))}
      </div>
      <div className="month-grid">
        {Array.from({ length: 35 }, (_, index) => {
          const date = index - 2;
          const eventDay = Object.keys(dayMap).find((key) => dayMap[key] === date);
          const dayEvents = eventDay
            ? events.filter((event) => event.day === eventDay)
            : [];
          return (
            <motion.button
              key={index}
              className={`month-cell ${date === 21 ? "is-today" : ""}`}
              whileHover={{ backgroundColor: "rgba(255,255,255,.035)" }}
              onClick={() => dayEvents[0] && setSelectedId(dayEvents[0].id)}
            >
              <span>{date > 0 && date <= 31 ? date : ""}</span>
              {dayEvents.slice(0, 2).map((event) => (
                <i
                  key={event.id}
                  className={selectedId === event.id ? "selected" : ""}
                  style={{
                    "--accent": toneMap[event.tone].accent,
                    "--accent-rgb": toneMap[event.tone].rgb,
                  }}
                >
                  {event.title}
                </i>
              ))}
              {dayEvents.length > 2 && <small>+{dayEvents.length - 2}</small>}
            </motion.button>
          );
        })}
      </div>
    </motion.div>
  );
}

function DeadlineEditor({ value, onSave }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value?.slice(0, 16) || "");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setDraft(value?.slice(0, 16) || "");
    setEditing(false);
  }, [value]);

  const save = async (nextValue) => {
    setSaving(true);
    try {
      await onSave(nextValue);
      setEditing(false);
    } catch {
      // The parent shows the persistence error and restores the old value.
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="detail-deadline-block">
      <div className="detail-deadline">
        <span className="deadline-symbol">
          <Clock3 size={12} />
        </span>
        <span className="deadline-copy">
          <small>截止时间</small>
          <strong>{value ? formatDeadline(value) : "无截止时间"}</strong>
        </span>
        {!editing && (
          <button onClick={() => setEditing(true)}>
            {value ? "修改" : "设置"}
          </button>
        )}
      </div>
      <AnimatePresence>
        {editing && (
          <motion.div
            className="deadline-editor"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            <input
              type="datetime-local"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              aria-label="设置截止时间"
            />
            <button
              className="deadline-save"
              disabled={!draft || saving}
              onClick={() => save(draft)}
            >
              保存
            </button>
            <button
              className="deadline-clear"
              disabled={!value || saving}
              onClick={() => save(null)}
            >
              清除
            </button>
            <button
              className="deadline-cancel"
              onClick={() => {
                setDraft(value?.slice(0, 16) || "");
                setEditing(false);
              }}
              aria-label="取消修改"
            >
              <X size={11} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function FocusRail({
  selectedEvent,
  onStartFocus,
  onPomodoroEvent,
  onUpdateDeadline,
  musicRecommendation,
  musicStatus,
  onMusicRefresh,
}) {
  const phaseDurations = { focus: 25 * 60, break: 10 * 60 };
  const [phase, setPhase] = useState("focus");
  const [secondsLeft, setSecondsLeft] = useState(phaseDurations.focus);
  const [isRunning, setIsRunning] = useState(false);
  const [completedFocusSessions, setCompletedFocusSessions] = useState(0);

  useEffect(() => {
    if (!isRunning) return undefined;
    const timer = window.setTimeout(() => {
      if (secondsLeft > 1) {
        setSecondsLeft((value) => value - 1);
        return;
      }
      if (phase === "focus") {
        setCompletedFocusSessions((value) => value + 1);
        setPhase("break");
        setSecondsLeft(phaseDurations.break);
        onPomodoroEvent?.("25 分钟专注完成，放松 10 分钟");
      } else {
        setPhase("focus");
        setSecondsLeft(phaseDurations.focus);
        onPomodoroEvent?.("放松结束，开始下一轮专注");
      }
    }, 1000);
    return () => window.clearTimeout(timer);
  }, [isRunning, secondsLeft, phase, onPomodoroEvent]);

  const phaseDuration = phaseDurations[phase];
  const progress = secondsLeft / phaseDuration;
  const minutes = String(Math.floor(secondsLeft / 60)).padStart(2, "0");
  const secs = String(secondsLeft % 60).padStart(2, "0");
  const selectedTone = selectedEvent ? toneMap[selectedEvent.tone] : toneMap.lime;
  const recommendedSong = musicRecommendation?.recommendation;
  const isBreak = phase === "break";
  const phaseLabel = isBreak ? "放松" : "专注";

  const selectPhase = (nextPhase) => {
    setPhase(nextPhase);
    setSecondsLeft(phaseDurations[nextPhase]);
    setIsRunning(false);
  };

  const resetCurrentPhase = () => {
    setSecondsLeft(phaseDuration);
    setIsRunning(false);
  };

  return (
    <motion.aside
      className="focus-rail"
      initial={{ opacity: 0, x: 22 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3, duration: 0.6 }}
    >
      <TiltCard
        className={`pulse-card pomodoro-card ${
          isBreak ? "break-mode" : "focus-mode"
        } ${isRunning ? "timer-running" : ""}`}
      >
        <div className="pulse-glow" />
        <div className="rail-card-head">
          <div>
            <span className="eyebrow tiny">POMODORO</span>
            <h3>番茄专注</h3>
          </div>
          <button
            className="pause-button reset-button"
            onClick={resetCurrentPhase}
            aria-label={`重置${phaseLabel}计时`}
            title={`重置${phaseLabel}计时`}
          >
            <TimerReset size={15} />
          </button>
        </div>
        <div className="pomodoro-mode-tabs">
          <button
            className={!isBreak ? "active" : ""}
            onClick={() => selectPhase("focus")}
          >
            <span>25</span> 专注
          </button>
          <button
            className={isBreak ? "active" : ""}
            onClick={() => selectPhase("break")}
          >
            <span>10</span> 放松
          </button>
        </div>
        <div
          className="timer-wrap"
          aria-label={`${phaseLabel}剩余 ${minutes} 分 ${secs} 秒`}
        >
          <svg viewBox="0 0 190 190" aria-hidden="true">
            <defs>
              <linearGradient id="timerGradient" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#dfff96" />
                <stop offset="100%" stopColor="#72e4c4" />
              </linearGradient>
            </defs>
            <circle className="timer-track" cx="95" cy="95" r="78" />
            <motion.circle
              className="timer-progress"
              cx="95"
              cy="95"
              r="78"
              initial={{ pathLength: 1 }}
              animate={{ pathLength: progress }}
              transition={{ duration: 0.35, ease: "linear" }}
            />
          </svg>
          <div className="timer-time">
            <span>{isBreak ? "RELAX SESSION" : "FOCUS SESSION"}</span>
            <strong>
              {minutes}<i>:</i>{secs}
            </strong>
            <small>{isRunning ? `${phaseLabel}进行中` : "准备开始一轮番茄"}</small>
          </div>
          <motion.span
            className="timer-orbit"
            animate={isRunning ? { rotate: 360 } : { rotate: 0 }}
            transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
          >
            <i />
          </motion.span>
        </div>
        <div className="pulse-footer">
          <div>
            <span>完成番茄</span>
            <strong>{String(completedFocusSessions).padStart(2, "0")}</strong>
          </div>
          <span className="pomodoro-cycle">25 + 10</span>
          <button
            className="pomodoro-toggle"
            onClick={() => setIsRunning((value) => !value)}
          >
            {isRunning ? <Pause size={11} /> : <Play size={11} />}
            {isRunning
              ? "暂停"
              : secondsLeft < phaseDuration
                ? "继续"
                : `开始${phaseLabel}`}
          </button>
        </div>
      </TiltCard>

      <div className="rail-section-head">
        <h3>接下来</h3>
        <button>全部 <ChevronRight size={13} /></button>
      </div>
      <AnimatePresence mode="wait">
        {selectedEvent ? (
          <motion.div
            key={selectedEvent.id}
            className="detail-card"
            initial={{ opacity: 0, y: 12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={spring}
            style={{
              "--accent": selectedTone.accent,
              "--accent-rgb": selectedTone.rgb,
            }}
          >
            <div className="detail-top">
              <span className="detail-day">已选中</span>
              <button>
                <Ellipsis size={16} />
              </button>
            </div>
            <span className="detail-time">
              <Clock3 size={13} /> {selectedEvent.time} · {selectedEvent.duration}
            </span>
            <h4>{selectedEvent.title}</h4>
            <p>{selectedEvent.meta}</p>
            {!selectedEvent.isMusic && (
              <DeadlineEditor
                value={selectedEvent.deadline}
                onSave={(deadline) =>
                  onUpdateDeadline(selectedEvent.id, deadline)
                }
              />
            )}
            {selectedEvent.isMusic ? (
              <div className="detail-music-meta">
                <span>
                  <Music2 size={12} />
                  本地歌单随机推荐
                </span>
                <button onClick={onMusicRefresh}>换一首</button>
              </div>
            ) : (
              <div className="attendees-row">
                <div className="avatar-stack">
                  <span>Y</span>
                  <span>M</span>
                  <span>+3</span>
                </div>
                <span>设计核心组</span>
              </div>
            )}
            <button
              className="detail-action"
              onClick={selectedEvent.isMusic ? onMusicRefresh : onStartFocus}
            >
              {selectedEvent.isMusic ? (
                <RefreshCw size={14} />
              ) : (
                <CornerDownLeft size={14} />
              )}
              {selectedEvent.isMusic ? "随机换一首" : "打开详情"}
            </button>
          </motion.div>
        ) : (
          <motion.div
            className="next-card"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="next-time">
              <span>14</span>
              <i>:</i>
              <span>30</span>
            </div>
            <div>
              <span className="eyebrow tiny">UP NEXT · 1 HR</span>
              <h4>设计批评会</h4>
              <p>Studio · 12 人</p>
            </div>
            <motion.span
              className="next-arrow"
              animate={{ x: [0, 4, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <ArrowDownRight size={18} />
            </motion.span>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        className={`daily-music-card ${musicStatus}`}
        whileHover={{ y: -2 }}
        transition={spring}
      >
        <div className={`daily-music-disc ${musicStatus === "ready" ? "playing" : ""}`}>
          <Music2 size={15} />
        </div>
        <div className="daily-music-copy">
          <span className="eyebrow tiny">DAILY SOUNDTRACK</span>
          {recommendedSong ? (
            <>
              <h4>{recommendedSong.title}</h4>
              <p>{recommendedSong.artist} · 个人日常随机推荐</p>
            </>
          ) : (
            <>
              <h4>
                {musicStatus === "offline" ? "本地歌单未连接" : "正在读取歌单…"}
              </h4>
              <p>
                {musicStatus === "offline"
                  ? "运行 npm run music:api 后重试"
                  : "扫描本地音乐库"}
              </p>
            </>
          )}
        </div>
        <button
          onClick={onMusicRefresh}
          className={musicStatus === "refreshing" ? "is-spinning" : ""}
          disabled={musicStatus === "refreshing"}
          aria-label="重新随机推荐"
          title="重新随机推荐"
        >
          <RefreshCw size={12} />
        </button>
      </motion.div>

      <motion.div className="note-card" whileHover={{ y: -3 }} transition={spring}>
        <div className="note-spark">
          <Sparkles size={16} />
        </div>
        <div>
          <span className="eyebrow tiny">ORBIT NOTE</span>
          <p>把 14:30 的会议缩短 15 分钟，你会有更完整的晚间留白。</p>
          <button>采纳建议 <ArrowUpRight size={12} /></button>
        </div>
      </motion.div>
      <div className="sync-status">
        <span><span className="sync-dot" />所有设备已同步</span>
        <span>刚刚</span>
      </div>
    </motion.aside>
  );
}

function AddEventModal({ isOpen, onClose, onAdd, initialDay }) {
  const [title, setTitle] = useState("");
  const [day, setDay] = useState(initialDay || "wed");
  const [time, setTime] = useState("16:30");
  const [deadline, setDeadline] = useState("");
  const [type, setType] = useState("work");
  const inputRef = useRef(null);
  const activeCategory = categoryMeta[type];

  useEffect(() => {
    if (!isOpen) return;
    setDay(initialDay || "wed");
    setDeadline("");
    window.setTimeout(() => inputRef.current?.focus(), 220);
  }, [isOpen, initialDay]);

  const submit = (event) => {
    event.preventDefault();
    if (!title.trim()) return;
    onAdd({
      title: title.trim(),
      day,
      time,
      type,
      deadline: deadline || null,
      duration: "30 MIN",
      meta: "新建日程 · 待补充",
      tone: activeCategory.tone,
    });
    setTitle("");
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) onClose();
          }}
        >
          <motion.form
            className="add-modal"
            onSubmit={submit}
            initial={{ opacity: 0, y: 28, scale: 0.95, rotateX: -4 }}
            animate={{ opacity: 1, y: 0, scale: 1, rotateX: 0 }}
            exit={{ opacity: 0, y: 18, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 330, damping: 30 }}
          >
            <div className="modal-glow" />
            <div className="modal-head">
              <div>
                <span className="eyebrow tiny">NEW BLOCK</span>
                <h2>插入一段新节奏</h2>
              </div>
              <button type="button" className="icon-button" onClick={onClose}>
                <X size={18} />
              </button>
            </div>
            <label className="field-label">
              日程名称
              <div className="modal-input-wrap">
                <Sparkles size={17} />
                <input
                  ref={inputRef}
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="例如：构思下一版体验..."
                />
              </div>
            </label>
            <div className="modal-grid">
              <label className="field-label">
                日期
                <select value={day} onChange={(event) => setDay(event.target.value)}>
                  {dayData.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.weekday} · 10/{item.date}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field-label">
                开始时间
                <input
                  type="time"
                  value={time}
                  onChange={(event) => setTime(event.target.value)}
                />
              </label>
            </div>
            <div className="deadline-row">
              <label className="field-label">
                截止时间（可选）
                <input
                  type="datetime-local"
                  value={deadline}
                  onChange={(event) => setDeadline(event.target.value)}
                />
              </label>
              <button
                type="button"
                className={`deadline-none ${deadline ? "" : "active"}`}
                onClick={() => setDeadline("")}
              >
                <Check size={12} />
                无截止时间
              </button>
            </div>
            <div className="field-label">
              日程类型
              <div className="type-options">
                {Object.entries(categoryMeta).map(([id, item]) => {
                  const tone = toneMap[item.tone];
                  return (
                    <button
                      type="button"
                      key={id}
                      className={type === id ? "active" : ""}
                      style={{
                        "--option-accent": tone.accent,
                        "--option-rgb": tone.rgb,
                      }}
                      onClick={() => setType(id)}
                    >
                      <i className={`type-dot ${id}`} />
                      {item.label}
                      {type === id && <Check size={13} />}
                    </button>
                  );
                })}
              </div>
              <AnimatePresence mode="wait">
                <motion.p
                  className="type-hint"
                  key={type}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  style={{ color: toneMap[activeCategory.tone].accent }}
                >
                  {activeCategory.hint}
                </motion.p>
              </AnimatePresence>
            </div>
            <div className="modal-footer">
              <span>
                <Command size={12} /> Enter 快速创建
              </span>
              <button type="submit" className="primary-button" disabled={!title.trim()}>
                创建日程
                <ArrowUpRight size={15} />
              </button>
            </div>
          </motion.form>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function GitHubSyncModal({ isOpen, onClose, onSync }) {
  const [profile, setProfile] = useState(
    () => window.localStorage.getItem("orbit.githubProfile") || "",
  );
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!isOpen) return;
    setError("");
    setResult(null);
    setStatus("idle");
    setToken("");
    setShowToken(false);
  }, [isOpen]);

  const submit = async (event) => {
    event.preventDefault();
    if (!profile.trim()) return;
    setStatus("syncing");
    setError("");
    try {
      const syncResult = await onSync(profile.trim(), token.trim());
      window.localStorage.setItem("orbit.githubProfile", profile.trim());
      setResult(syncResult);
      setStatus("success");
    } catch (syncError) {
      setError(syncError.message || "GitHub 同步失败。");
      setStatus("error");
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) onClose();
          }}
        >
          <motion.form
            className="add-modal github-modal"
            onSubmit={submit}
            initial={{ opacity: 0, y: 28, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 18, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 330, damping: 30 }}
          >
            <div className="modal-glow github-glow" />
            <div className="modal-head">
              <div>
                <span className="eyebrow tiny">GITHUB TRACKER</span>
                <h2>把近期提交变成工作日程</h2>
              </div>
              <button type="button" className="icon-button" onClick={onClose}>
                <X size={18} />
              </button>
            </div>
            <label className="field-label">
              GitHub 个人主页
              <div className="modal-input-wrap github-input">
                <Github size={17} />
                <input
                  value={profile}
                  onChange={(event) => setProfile(event.target.value)}
                  placeholder="https://github.com/username"
                  autoFocus
                />
              </div>
            </label>
            <label className="field-label github-token-label">
              GitHub Token（可选）
              <div className="modal-input-wrap github-token-input">
                <KeyRound size={17} />
                <input
                  type={showToken ? "text" : "password"}
                  value={token}
                  onChange={(event) => setToken(event.target.value)}
                  placeholder="github_pat_..."
                  autoComplete="off"
                  spellCheck="false"
                />
                <button
                  type="button"
                  className="token-visibility"
                  onClick={() => setShowToken((value) => !value)}
                  aria-label={showToken ? "隐藏 Token" : "显示 Token"}
                >
                  {showToken ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </label>
            <div className="github-sync-note">
              <div>
                <span>PUBLIC ONLY</span>
                <strong>仅读取公开仓库</strong>
              </div>
              <div>
                <span>LOOKBACK</span>
                <strong>最近 21 天</strong>
              </div>
              <div>
                <span>OUTPUT</span>
                <strong>工作事务</strong>
              </div>
            </div>
            <p className="github-help">
              会检查仓库中由该用户提交的记录。未填写 Token 时，会尝试使用后端
              <code> GITHUB_TOKEN </code>
              环境变量；两者都没有时受公开 API 频率限制。
            </p>
            <details className="github-token-help">
              <summary>
                <ShieldCheck size={13} />
                如何生成 GitHub Token
                <ChevronRight size={12} />
              </summary>
              <ol>
                <li>
                  打开 GitHub 的
                  <a
                    href="https://github.com/settings/personal-access-tokens/new"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Fine-grained token 页面
                    <ExternalLink size={10} />
                  </a>
                </li>
                <li>在 Token name 中填写容易识别的名称，并设置过期时间。</li>
                <li>
                  Repository access 选择 <strong>Public repositories</strong>
                  （只读）。
                </li>
                <li>
                  Repository permissions 中把 <strong>Contents</strong> 设为
                  <strong>Read-only</strong>，Metadata 会自动获得只读权限。
                </li>
                <li>
                  点击 Generate token，复制
                  <code>github_pat_...</code>
                  并粘贴到上方输入框。
                </li>
              </ol>
              <p>
                Token 只保留在当前页面内存中，关闭弹窗或刷新页面后即清空，不会写入项目文件。
                请勿把真实 Token 截图或提交到代码仓库。
              </p>
            </details>
            <AnimatePresence mode="wait">
              {error && (
                <motion.p
                  key="error"
                  className="github-error"
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  {error}
                </motion.p>
              )}
              {result && (
                <motion.div
                  key="result"
                  className="github-result"
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  <span>
                    <Check size={12} /> 已找到 {result.repositories.length} 个活跃仓库
                  </span>
                  <small>
                    新建 {result.created} · 更新 {result.updated} · 清理{" "}
                    {result.removed}
                    {result.truncated ? " · 结果已截断" : ""}
                  </small>
                </motion.div>
              )}
            </AnimatePresence>
            <div className="modal-footer">
              <span>
                <CircleDot size={10} /> 重复同步不会产生重复日程
              </span>
              <button
                type="submit"
                className="primary-button"
                disabled={!profile.trim() || status === "syncing"}
              >
                {status === "syncing" ? (
                  <RefreshCw className="spin-icon" size={15} />
                ) : (
                  <Github size={15} />
                )}
                {status === "syncing" ? "正在扫描…" : "同步工作日程"}
              </button>
            </div>
          </motion.form>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function MusicLibraryModal({ isOpen, onClose, onImport, currentSource }) {
  const [path, setPath] = useState("");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!isOpen) return;
    setPath(currentSource?.activePath || "");
    setError("");
    setResult(null);
    setStatus("idle");
  }, [isOpen, currentSource?.activePath]);

  const submit = async (event) => {
    event.preventDefault();
    if (!path.trim()) return;
    setStatus("importing");
    setError("");
    try {
      const imported = await onImport(path.trim());
      setResult(imported);
      setStatus("success");
    } catch (importError) {
      setError(importError.message || "本地音乐库导入失败。");
      setStatus("error");
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) onClose();
          }}
        >
          <motion.form
            className="add-modal github-modal music-library-modal"
            onSubmit={submit}
            initial={{ opacity: 0, y: 28, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 18, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 330, damping: 30 }}
          >
            <div className="modal-glow music-library-glow" />
            <div className="modal-head">
              <div>
                <span className="eyebrow tiny">LOCAL MUSIC</span>
                <h2>接入你的本地音乐库</h2>
              </div>
              <button type="button" className="icon-button" onClick={onClose}>
                <X size={18} />
              </button>
            </div>
            <label className="field-label">
              歌单文件或音乐目录
              <div className="modal-input-wrap music-source-input">
                <FolderOpen size={17} />
                <input
                  value={path}
                  onChange={(event) => setPath(event.target.value)}
                  placeholder="~/Music 或 ~/Music/weekly.m3u"
                  autoFocus
                />
              </div>
            </label>
            <div className="github-sync-note music-source-notes">
              <div>
                <span>LOCAL ONLY</span>
                <strong>本机路径</strong>
              </div>
              <div>
                <span>FORMATS</span>
                <strong>歌单或目录</strong>
              </div>
              <div>
                <span>FEEDS</span>
                <strong>个人日常</strong>
              </div>
            </div>
            <p className="github-help">
              支持 M3U、PLS、JSON、CSV、TXT 歌单，也可直接指向包含
              MP3、FLAC、M4A、WAV 等文件的目录。路径由本机 Python
              服务读取，浏览器不会上传音频文件。
            </p>
            {currentSource?.playlist && !result && (
              <div className="current-music-source">
                <span>
                  <Music2 size={12} /> 当前曲库
                </span>
                <strong>
                  {currentSource.playlist.name} · {currentSource.playlist.total} 首
                </strong>
              </div>
            )}
            <AnimatePresence mode="wait">
              {error && (
                <motion.p
                  key="error"
                  className="github-error"
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  {error}
                </motion.p>
              )}
              {result?.playlist && (
                <motion.div
                  key="result"
                  className="github-result music-import-result"
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  <span>
                    <Check size={12} /> 已读取 {result.playlist.total} 首歌曲
                  </span>
                  <small>{result.playlist.name}</small>
                </motion.div>
              )}
            </AnimatePresence>
            <div className="modal-footer">
              <span>
                <CircleDot size={10} /> 选择后自动保存
              </span>
              <button
                type="submit"
                className="primary-button"
                disabled={!path.trim() || status === "importing"}
              >
                {status === "importing" ? (
                  <RefreshCw className="spin-icon" size={15} />
                ) : (
                  <FolderOpen size={15} />
                )}
                {status === "importing" ? "正在读取…" : "导入音乐库"}
              </button>
            </div>
          </motion.form>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function AmbientBackground() {
  const reducedMotion = useReducedMotion();
  return (
    <div className="ambient-background" aria-hidden="true">
      <motion.div
        className="ambient-glow glow-lime"
        animate={
          reducedMotion
            ? {}
            : { x: [0, 36, -12, 0], y: [0, -24, 20, 0], scale: [1, 1.1, 0.96, 1] }
        }
        transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="ambient-glow glow-violet"
        animate={
          reducedMotion
            ? {}
            : { x: [0, -28, 18, 0], y: [0, 26, -10, 0], scale: [1, 0.92, 1.08, 1] }
        }
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="ambient-glow glow-orange"
        animate={reducedMotion ? {} : { x: [0, 20, -18, 0], y: [0, 18, -22, 0] }}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
      />
      <div className="grain" />
      <div className="ambient-grid" />
    </div>
  );
}

function Toast({ message }) {
  return (
    <AnimatePresence>
      {message && (
        <motion.div
          className="toast"
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 12, scale: 0.96 }}
        >
          <span><Check size={14} /></span>
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default function App() {
  const [events, setEvents] = useState([]);
  const [filter, setFilter] = useState("all");
  const [view, setView] = useState("周");
  const [selectedId, setSelectedId] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isGithubModalOpen, setIsGithubModalOpen] = useState(false);
  const [isMusicModalOpen, setIsMusicModalOpen] = useState(false);
  const [modalDay, setModalDay] = useState("wed");
  const [toast, setToast] = useState("");
  const [musicRecommendation, setMusicRecommendation] = useState(null);
  const [musicStatus, setMusicStatus] = useState("loading");
  const [musicSource, setMusicSource] = useState(null);
  const [scheduleStatus, setScheduleStatus] = useState("loading");

  const requestMusicRecommendation = async (avoidId = "") => {
    setMusicStatus(musicRecommendation ? "refreshing" : "loading");
    try {
      const query = avoidId ? `?avoid=${encodeURIComponent(avoidId)}` : "";
      const payload = await orbitApi(`/api/recommendation${query}`);
      if (!payload?.recommendation) {
        throw new Error("Music API returned no recommendation");
      }
      setMusicRecommendation(payload);
      setMusicStatus("ready");
    } catch {
      setMusicStatus("offline");
    }
  };

  useEffect(() => {
    requestMusicRecommendation();
    orbitApi("/api/music/source")
      .then(setMusicSource)
      .catch(() => {});
    // Run once on mount; subsequent rolls use the latest recommendation as `avoid`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let cancelled = false;
    orbitApi("/api/schedules")
      .then((payload) => {
        if (cancelled) return;
        const loadedEvents = (payload.items || [])
          .map(scheduleToEvent)
          .filter(Boolean);
        setEvents(loadedEvents);
        setSelectedId(
          (current) =>
            current ||
            loadedEvents.find((event) => event.id === "sch-design-critique")?.id ||
            loadedEvents[0]?.id ||
            null,
        );
        setScheduleStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setScheduleStatus("offline");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const boardEvents = useMemo(() => {
    const musicEvent = musicEventFromPayload(musicRecommendation);
    return musicEvent ? [...events, musicEvent] : events;
  }, [events, musicRecommendation]);

  const selectedEvent = boardEvents.find((event) => event.id === selectedId);
  const todayEventCount = boardEvents.filter((event) => event.day === "wed").length;

  const showToast = (message) => {
    setToast(message);
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => setToast(""), 2600);
  };

  const moveEvent = async (id, day) => {
    const existing = events.find((event) => event.id === id);
    if (!existing) return;
    const previous = events;
    setEvents((current) =>
      current.map((event) => (event.id === id ? { ...event, day } : event)),
    );
    setScheduleStatus("saving");
    try {
      const saved = await orbitApi(`/api/schedules/${encodeURIComponent(id)}`, {
        method: "PATCH",
        body: JSON.stringify({ date: dayToIsoDate(day) }),
      });
      const updated = scheduleToEvent(saved);
      setEvents((current) =>
        current.map((event) => (event.id === id ? updated : event)),
      );
      setScheduleStatus("ready");
      showToast("日程已移动并保存");
    } catch {
      setEvents(previous);
      setScheduleStatus("offline");
      showToast("移动失败，日程已恢复");
    }
  };

  const addEvent = async (payload) => {
    setScheduleStatus("saving");
    try {
      const saved = await orbitApi("/api/schedules", {
        method: "POST",
        body: JSON.stringify({
          type: payload.type,
          title: payload.title,
          date: dayToIsoDate(payload.day),
          startTime: payload.time,
          durationMinutes: 30,
          deadline: payload.deadline || null,
          description: payload.meta || "新建日程 · 待补充",
          status: "planned",
        }),
      });
      const newEvent = scheduleToEvent(saved);
      setEvents((current) => [...current, newEvent]);
      setSelectedId(newEvent.id);
      setScheduleStatus("ready");
      showToast(`「${payload.title}」已保存到本地`);
    } catch {
      setScheduleStatus("offline");
      showToast("新建失败，请确认本地 API 已启动");
    }
  };

  const toggleScheduleStatus = async (id) => {
    const existing = events.find((event) => event.id === id);
    if (!existing) return;
    const nextStatus = existing.status === "done" ? "planned" : "done";
    const previous = events;
    setEvents((current) =>
      current.map((event) =>
        event.id === id ? { ...event, status: nextStatus } : event,
      ),
    );
    setScheduleStatus("saving");
    try {
      const saved = await orbitApi(`/api/schedules/${encodeURIComponent(id)}`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus }),
      });
      setEvents((current) =>
        current.map((event) =>
          event.id === id ? scheduleToEvent(saved) : event,
        ),
      );
      setScheduleStatus("ready");
    } catch {
      setEvents(previous);
      setScheduleStatus("offline");
      showToast("状态保存失败，已恢复");
    }
  };

  const updateDeadline = async (id, deadline) => {
    const previous = events;
    setEvents((current) =>
      current.map((event) =>
        event.id === id ? { ...event, deadline: deadline || null } : event,
      ),
    );
    setScheduleStatus("saving");
    try {
      const saved = await orbitApi(`/api/schedules/${encodeURIComponent(id)}`, {
        method: "PATCH",
        body: JSON.stringify({ deadline }),
      });
      setEvents((current) =>
        current.map((event) =>
          event.id === id ? scheduleToEvent(saved) : event,
        ),
      );
      setScheduleStatus("ready");
      showToast(deadline ? "截止时间已保存" : "已设为无截止时间");
      return saved;
    } catch (error) {
      setEvents(previous);
      setScheduleStatus("offline");
      showToast("截止时间保存失败，已恢复");
      throw error;
    }
  };

  const openAdd = (day = "wed") => {
    setModalDay(day);
    setIsModalOpen(true);
  };

  const startFocus = () => {
    showToast("专注模式已准备就绪");
  };

  const syncGithub = async (profile, token) => {
    const result = await orbitApi("/api/github/sync", {
      method: "POST",
      body: JSON.stringify({ profile, token }),
    });
    const loadedEvents = (result.schedules || [])
      .map(scheduleToEvent)
      .filter(Boolean);
    setEvents(loadedEvents);
    setScheduleStatus("ready");
    setSelectedId(
      (current) =>
        current ||
        loadedEvents.find((event) => event.id === "sch-design-critique")?.id ||
        loadedEvents[0]?.id ||
        null,
    );
    showToast(`GitHub 同步完成：${result.repositories.length} 个活跃仓库`);
    return result;
  };

  const importMusicLibrary = async (path) => {
    const source = await orbitApi("/api/music/source", {
      method: "POST",
      body: JSON.stringify({ path }),
    });
    setMusicSource(source);
    await requestMusicRecommendation();
    showToast(`已导入 ${source.playlist.total} 首歌曲`);
    return source;
  };

  return (
    <div className="app-shell">
      <AmbientBackground />
      <Sidebar
        isOpen={isSidebarOpen}
        setIsOpen={setIsSidebarOpen}
        scheduleCount={boardEvents.length}
      />
      <div className="app-main">
        <Topbar onMenu={() => setIsSidebarOpen(true)} />
        <div className="dashboard">
          <Greeting onAdd={() => openAdd("wed")} eventCount={todayEventCount} />
          <div className="dashboard-grid">
            <Board
              events={boardEvents}
              selectedId={selectedId}
              setSelectedId={setSelectedId}
              filter={filter}
              setFilter={setFilter}
              onMove={moveEvent}
              onAdd={openAdd}
              onToggleStatus={toggleScheduleStatus}
              scheduleStatus={scheduleStatus}
              onOpenGithub={() => setIsGithubModalOpen(true)}
              onOpenMusic={() => setIsMusicModalOpen(true)}
              onMusicRefresh={() =>
                requestMusicRecommendation(musicRecommendation?.recommendation?.id)
              }
              musicStatus={musicStatus}
              view={view}
              setView={setView}
            />
            <FocusRail
              selectedEvent={selectedEvent}
              onStartFocus={startFocus}
              onPomodoroEvent={showToast}
              onUpdateDeadline={updateDeadline}
              musicRecommendation={musicRecommendation}
              musicStatus={musicStatus}
              onMusicRefresh={() =>
                requestMusicRecommendation(musicRecommendation?.recommendation?.id)
              }
            />
          </div>
        </div>
      </div>
      <AddEventModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onAdd={addEvent}
        initialDay={modalDay}
      />
      <GitHubSyncModal
        isOpen={isGithubModalOpen}
        onClose={() => setIsGithubModalOpen(false)}
        onSync={syncGithub}
      />
      <MusicLibraryModal
        isOpen={isMusicModalOpen}
        onClose={() => setIsMusicModalOpen(false)}
        onImport={importMusicLibrary}
        currentSource={musicSource}
      />
      <Toast message={toast} />
    </div>
  );
}
