# ============================================================
# 고교 공부 메이트
# 기능: 과목별 스톱워치로 순공 시간 측정 + 시험 D-Day 표시
# 사용 라이브러리: 전부 파이썬 기본 내장 
# ============================================================

import calendar   # 달력(몇 주, 요일 배치) 계산용
import datetime   # 날짜 계산용 (오늘 날짜, D-Day 등)
import json       # 데이터를 파일로 저장/불러오기 (JSON 형식)
import os         # 파일 경로 다루기
import sys        # 어떤 OS(Windows/Mac)에서 실행 중인지 확인용
import time       # 스톱워치용 시간 측정
import tkinter as tk              # 화면(GUI)을 만드는 기본 라이브러리
from tkinter import messagebox    # "정말 삭제할까요?" 같은 알림창

# ---------- 디자인 설정 ----------
# 색상/글꼴을 맨 위에 모아두면, 나중에 디자인을 바꿀 때 여기만 고치면 돼요.
FONT = "맑은 고딕"
BG = "#eef1f6"          # 전체 배경
CARD = "#ffffff"        # 팝업 배경
BORDER = "#e3e7ee"      # 구분선 색
TEXT = "#1f2937"        # 기본 글자색
MUTED = "#8b94a5"       # 흐린 글자색 (설명 문구용)
PRIMARY = "#4f6df5"             # 메인 파란색
PRIMARY_HOVER = "#3f5ce0"       # 파란 버튼에 마우스를 올렸을 때
PRIMARY_SOFT = "#e3eaff"        # 연한 파란색 (배경용)
PRIMARY_SOFT_HOVER = "#d3ddff"
DANGER = "#ef4444"              # 빨간색 (정지, 경고)
DANGER_HOVER = "#dc2626"
DANGER_SOFT = "#fee2e2"         # 연한 빨간색
SUCCESS = "#16a34a"             # 초록색 (공부 중 표시)
SUCCESS_SOFT = "#dcfce7"
WARN = "#b45309"                # 주황/갈색 (일시정지 표시)
WARN_SOFT = "#fef3c7"
GRAY = "#dde1ea"                # 회색 버튼
GRAY_HOVER = "#cdd2dd"

# 과목별 색상 (과목 순서대로 돌아가며 사용)
SUBJECT_COLORS = [
    "#4f6df5", "#f59e0b", "#10b981", "#ef4444",
    "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16",
]
# 처음 실행했을 때 기본으로 들어있는 과목들
DEFAULT_SUBJECTS = ["국어", "수학", "영어", "과학", "사회"]

# ---------- 동작 설정 ----------
# 숫자를 코드 곳곳에 직접 쓰지 않고 이름을 붙여 모아두면 나중에 고치기 편해요.
MAX_SUBJECTS = 12          # 과목 최대 개수
AUTOSAVE_SECONDS = 30      # 공부 중 자동 저장 간격(초)
TICK_MS = 200              # 스톱워치 화면 갱신 간격 (0.2초)
AUTO_REFRESH_MS = 60000    # D-Day/기록 새로고침 간격 (1분)
SLEEP_GAP_SECONDS = 5      # 화면 갱신 사이가 이보다 길면 "절전/멈춤"으로 보고 그 시간은 뺌
DDAY_WARN_DAYS = 7         # D-Day가 이 값 이하로 남으면 배너를 빨간색으로 표시

# 공부 기록은 "내 사용자 폴더"에 저장해요. (Windows: C:\사용자\내이름\AppData\Roaming\GosuMate)
# 프로그램 파일(.exe) 옆에 저장하면, exe로 만들었을 때 껐다 켜면 기록이 사라질 수 있어요.
APP_DIR = os.path.join(
    os.environ.get("APPDATA") or os.path.expanduser("~"), "GosuMate"
)
try:
  os.makedirs(APP_DIR, exist_ok=True)   # 폴더가 없으면 만들고, 있으면 그냥 넘어가요
except OSError:
  pass
DATA_FILE = os.path.join(APP_DIR, "study_data.json")   # 공부 기록이 저장되는 파일
LEGACY_FILE = os.path.join(APP_DIR, "dday.json")  # 예전 버전 파일 (시험일만 불러옴)
# datetime의 weekday()는 월요일=0 ... 일요일=6 이라서 이 순서로 맞춰 둔 거예요.
WEEKDAYS_KR = ["월", "화", "수", "목", "금", "토", "일"]


# ---------- 도우미 함수 ----------
# 화면과 상관없이 "계산/변환"만 하는 함수들이에요.
def today_iso():
  # 오늘 날짜를 "2026-11-13" 같은 문자열로 돌려줘요. (기록 저장할 때 키로 사용)
  return datetime.date.today().isoformat()


def days_until(target_date):
  # 목표 날짜까지 며칠 남았는지 계산. 지났으면 음수가 나와요.
  return (target_date - datetime.date.today()).days


def make_dday_number(target_date):
  # "D-5", "D-Day", "D+3" 같은 짧은 D-Day 문자열 만들기
  days = days_until(target_date)
  if days > 0:
    return f"D-{days}"
  elif days == 0:
    return "D-Day"
  return f"D+{-days}"   # days가 음수이므로 -를 붙여 양수로 바꿔 표시


def make_dday_message(target_date):
  # 달력 팝업 미리보기에 보여줄 안내 문장
  days = days_until(target_date)
  if days > 0:
    return f"시험까지 {days}일 남았어요"
  elif days == 0:
    return "오늘이 바로 시험날이에요! 화이팅!"
  return f"시험일이 {-days}일 지났어요"


def make_banner_text(target_date):
  # 메인 화면 맨 위 배너에 보여줄 문장
  days = days_until(target_date)
  if days > 0:
    return f"시험까지 D-{days}일 남았습니다!"
  elif days == 0:
    return "오늘이 바로 시험 D-Day입니다! 화이팅!"
  return f"시험일이 {-days}일 지났습니다."


def format_date_kr(d):
  # 날짜를 "2026년 11월 19일 (목)" 형태로 바꿔줘요.
  return f"{d.year}년 {d.month}월 {d.day}일 ({WEEKDAYS_KR[d.weekday()]})"


def fmt_hms(seconds):
  # 초 단위 숫자를 "01:23:45" (시:분:초) 형태로 바꿔줘요.
  total = int(seconds)
  # // 는 몫, % 는 나머지. 예) 3725초 -> 1시간(3600) + 125초 -> 2분 5초
  h, m, s = total // 3600, (total % 3600) // 60, total % 60
  return f"{h:02d}:{m:02d}:{s:02d}"   # :02d = 두 자리로 맞추고 빈칸은 0으로 채움


def center_window(win, parent):
  # 팝업창을 부모(메인) 창의 가운데에 띄워요.
  win.update_idletasks()   # 창 크기를 먼저 계산시켜서 정확한 크기를 얻기 위함
  w, h = win.winfo_reqwidth(), win.winfo_reqheight()   # 팝업이 필요로 하는 크기
  x = parent.winfo_x() + (parent.winfo_width() - w) // 2
  y = parent.winfo_y() + (parent.winfo_height() - h) // 2
  win.geometry(f"+{max(x, 0)}+{max(y, 0)}")   # max(..., 0): 화면 밖으로 나가지 않게


def safe_grab(win):
  # grab_set = 이 팝업을 닫기 전까지 뒤쪽 창을 클릭 못 하게 막는 기능.
  # 가끔 오류가 날 수 있어서, 실패해도 프로그램이 멈추지 않게 try/except로 감싸요.
  try:
    win.grab_set()
  except tk.TclError:
    pass


class FlatButton(tk.Label):
  """마우스를 올리면 색이 바뀌는 평평한 버튼 (Windows/Mac 모두 색이 잘 보임)."""
  # tk.Button은 Mac에서 색이 잘 안 먹어서, Label을 버튼처럼 쓰는 방식이에요.

  def __init__(self, parent, text, command, bg, fg="white", hover=None,
               font=None, padx=18, pady=10, **kw):
    # 부모 클래스(Label)를 먼저 만들어요. 글자/색/여백/손모양 커서 설정
    super().__init__(
        parent, text=text, bg=bg, fg=fg, font=font or (FONT, 11, "bold"),
        padx=padx, pady=pady, cursor="hand2", **kw
    )
    self.command = command      # 클릭했을 때 실행할 함수
    self.normal_bg = bg         # 평소 배경색
    self.hover_bg = hover or bg # 마우스를 올렸을 때 색 (없으면 그대로)
    # <Enter> = 마우스가 올라옴, <Leave> = 마우스가 나감, <Button-1> = 왼쪽 클릭
    self.bind("<Enter>", lambda e: self.config(bg=self.hover_bg))
    self.bind("<Leave>", lambda e: self.config(bg=self.normal_bg))
    self.bind("<Button-1>", lambda e: self.command())


# ---------- 팝업: 시험 날짜 달력 ----------
class CalendarPopup(tk.Toplevel):
  # Toplevel = 메인 창 위에 뜨는 새 창(팝업)

  def __init__(self, parent, initial_date, on_select):
    super().__init__(parent)
    self.title("시험 날짜 선택")
    self.configure(bg=CARD)
    self.resizable(False, False)   # 크기 조절 불가
    self.transient(parent)         # 메인 창 위에 항상 붙어서 뜨게 함

    self.on_select = on_select           # 날짜 확정 시 호출할 함수(메인 앱이 넘겨줌)
    self.selected = initial_date         # 현재 선택된 날짜
    self.view_year = initial_date.year   # 지금 달력에 보이는 연도
    self.view_month = initial_date.month # 지금 달력에 보이는 월

    wrap = tk.Frame(self, bg=CARD)   # 내용을 담는 큰 상자(여백용)
    wrap.pack(padx=22, pady=20)

    # --- 상단: ◀ 2026년 11월 ▶ ---
    header = tk.Frame(wrap, bg=CARD)
    header.pack(fill="x", pady=(0, 10))
    FlatButton(
        header, "◀", self.prev_month, PRIMARY_SOFT, PRIMARY,
        PRIMARY_SOFT_HOVER, padx=10, pady=4
    ).pack(side="left")
    FlatButton(
        header, "▶", self.next_month, PRIMARY_SOFT, PRIMARY,
        PRIMARY_SOFT_HOVER, padx=10, pady=4
    ).pack(side="right")
    self.month_label = tk.Label(
        header, text="", font=(FONT, 14, "bold"), bg=CARD, fg=TEXT
    )
    self.month_label.pack(expand=True)

    # 날짜 버튼들이 들어갈 영역 (draw()가 여기에 날짜를 그려요)
    self.days_frame = tk.Frame(wrap, bg=CARD)
    self.days_frame.pack()

    # --- 구분선 + 선택한 날짜 미리보기 ---
    tk.Frame(wrap, bg=BORDER, height=1).pack(fill="x", pady=(14, 10))
    self.preview_date = tk.Label(
        wrap, text="", font=(FONT, 11), bg=CARD, fg=MUTED
    )
    self.preview_date.pack()
    self.preview_dday = tk.Label(
        wrap, text="", font=(FONT, 20, "bold"), bg=CARD, fg=PRIMARY
    )
    self.preview_dday.pack(pady=(2, 0))
    self.preview_msg = tk.Label(
        wrap, text="", font=(FONT, 10), bg=CARD, fg=TEXT
    )
    self.preview_msg.pack(pady=(0, 12))

    # --- 하단 버튼: 오늘로 이동 / 설정 완료 ---
    bottom = tk.Frame(wrap, bg=CARD)
    bottom.pack(fill="x")
    FlatButton(
        bottom, "오늘로 이동", self.go_today, GRAY, TEXT, GRAY_HOVER,
        font=(FONT, 10, "bold"), pady=8
    ).pack(side="left", expand=True, fill="x", padx=(0, 6))
    FlatButton(
        bottom, "설정 완료", self.confirm, PRIMARY, "white", PRIMARY_HOVER,
        font=(FONT, 10, "bold"), pady=8
    ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    self.draw()                  # 달력 그리기
    center_window(self, parent)  # 가운데에 배치
    safe_grab(self)              # 이 팝업을 닫기 전까지 뒤쪽 창 클릭 막기

  def draw(self):
    # 달력을 통째로 다시 그려요. (월 이동, 날짜 선택 때마다 호출됨)
    # 먼저 기존에 그려진 날짜 버튼들을 모두 지워요.
    for w in self.days_frame.winfo_children():
      w.destroy()

    self.month_label.config(text=f"{self.view_year}년 {self.view_month}월")

    # 요일 이름 줄 (일요일은 빨강, 토요일은 파랑, 나머지는 회색)
    for col, name in enumerate(["일", "월", "화", "수", "목", "금", "토"]):
      color = DANGER if col == 0 else PRIMARY if col == 6 else MUTED
      tk.Label(
          self.days_frame, text=name, width=4, font=(FONT, 10, "bold"),
          bg=CARD, fg=color
      ).grid(row=0, column=col, pady=(0, 6))

    today = datetime.date.today()
    cal = calendar.Calendar(firstweekday=6)  # 6 = 일요일 시작
    # 그 달을 주 단위 리스트로 받아요. 예: [[0,0,1,2,3,4,5], [6,7,...], ...]
    # 0은 "그 달이 아닌 빈칸"이라는 뜻이에요.
    weeks = cal.monthdayscalendar(self.view_year, self.view_month)
    for r, week in enumerate(weeks, start=1):   # 0번 줄은 요일 이름이라 1부터 시작
      for c, day in enumerate(week):
        if day == 0:
          continue   # 빈칸은 건너뜀
        d = datetime.date(self.view_year, self.view_month, day)
        # 기본 색: 일요일 빨강, 토요일 파랑, 평일 검정
        fg = DANGER if c == 0 else PRIMARY if c == 6 else TEXT
        bg, hover = CARD, PRIMARY_SOFT
        font = (FONT, 10)
        if d == today:   # 오늘 날짜는 초록으로 강조
          bg, hover, fg = SUCCESS_SOFT, SUCCESS_SOFT, SUCCESS
          font = (FONT, 10, "bold")
        if d == self.selected:   # 선택한 날짜는 파란 배경 (오늘보다 우선)
          bg, hover, fg = PRIMARY, PRIMARY_HOVER, "white"
          font = (FONT, 10, "bold")
        # lambda dd=d: ... 에서 dd=d 를 쓰는 이유: 반복문의 d 값을 그 순간 값으로
        # 고정해 두기 위해서예요. (안 쓰면 모든 버튼이 마지막 날짜를 가리켜요)
        FlatButton(
            self.days_frame, str(day), lambda dd=d: self.pick(dd), bg, fg,
            hover, font=font, padx=0, pady=7, width=4
        ).grid(row=r, column=c, padx=1, pady=1)

    self.update_preview()

  def update_preview(self):
    # 선택된 날짜에 맞춰 아래 미리보기 글자를 갱신
    self.preview_date.config(text=format_date_kr(self.selected))
    self.preview_dday.config(text=make_dday_number(self.selected))
    self.preview_msg.config(text=make_dday_message(self.selected))

  def pick(self, d):
    # 날짜 버튼을 눌렀을 때: 선택 날짜를 바꾸고 다시 그림
    self.selected = d
    self.draw()

  def prev_month(self):
    # ◀ 버튼: 이전 달로. 1월에서 더 내려가면 작년 12월로 넘어가요.
    self.view_month -= 1
    if self.view_month < 1:
      self.view_month = 12
      self.view_year -= 1
    self.draw()

  def next_month(self):
    # ▶ 버튼: 다음 달로. 12월에서 더 올라가면 내년 1월로 넘어가요.
    self.view_month += 1
    if self.view_month > 12:
      self.view_month = 1
      self.view_year += 1
    self.draw()

  def go_today(self):
    # "오늘로 이동": 달력 화면을 오늘이 있는 달로 옮겨요. (선택 날짜는 그대로)
    today = datetime.date.today()
    self.view_year = today.year
    self.view_month = today.month
    self.draw()

  def confirm(self):
    # "설정 완료": 메인 앱에서 넘겨준 함수에 선택한 날짜를 전달하고 팝업 닫기
    self.on_select(self.selected)
    self.destroy()


# ---------- 팝업: 과목 추가 ----------
class AddSubjectDialog(tk.Toplevel):

  def __init__(self, parent, on_add):
    super().__init__(parent)
    self.title("과목 추가")
    self.configure(bg=CARD)
    self.resizable(False, False)
    self.transient(parent)
    self.on_add = on_add   # 과목을 실제로 추가하는 함수 (메인 앱의 add_subject)

    wrap = tk.Frame(self, bg=CARD)
    wrap.pack(padx=24, pady=20)

    tk.Label(
        wrap, text="추가할 과목 이름", font=(FONT, 11, "bold"),
        bg=CARD, fg=TEXT
    ).pack(anchor="w")
    # 글자를 입력하는 칸
    self.entry = tk.Entry(
        wrap, font=(FONT, 12), relief="flat", bg=PRIMARY_SOFT, fg=TEXT,
        insertbackground=TEXT, highlightthickness=1,
        highlightbackground=BORDER, highlightcolor=PRIMARY, width=24
    )
    self.entry.pack(fill="x", pady=(8, 4), ipady=6)
    # 잘못 입력했을 때 빨간 글씨로 안내하는 자리
    self.error_label = tk.Label(
        wrap, text="", font=(FONT, 9), bg=CARD, fg=DANGER
    )
    self.error_label.pack(anchor="w", pady=(0, 8))

    row = tk.Frame(wrap, bg=CARD)
    row.pack(fill="x")
    FlatButton(
        row, "취소", self.destroy, GRAY, TEXT, GRAY_HOVER,
        font=(FONT, 10, "bold"), pady=8
    ).pack(side="left", expand=True, fill="x", padx=(0, 6))
    FlatButton(
        row, "추가", self.submit, PRIMARY, "white", PRIMARY_HOVER,
        font=(FONT, 10, "bold"), pady=8
    ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    # 엔터키 = 추가, ESC키 = 취소
    self.entry.bind("<Return>", lambda e: self.submit())
    self.bind("<Escape>", lambda e: self.destroy())

    center_window(self, parent)
    safe_grab(self)
    self.entry.focus_set()   # 열자마자 바로 타이핑할 수 있게 커서를 입력칸에 둠

  def submit(self):
    # on_add는 성공하면 None, 실패하면 오류 문구(문자열)를 돌려줘요.
    error = self.on_add(self.entry.get())
    if error:
      self.error_label.config(text=error)   # 실패: 팝업에 빨간 글씨로 이유 표시
    else:
      self.destroy()                        # 성공: 팝업 닫기


# ---------- 메인 앱 ----------
class StudyApp:

  def __init__(self, root):
    self.root = root   # root = 프로그램의 메인 창
    self.root.title("고교 공부 메이트")
    self.root.geometry("460x720")        # 창 크기 (가로x세로)
    self.root.minsize(460, 600)          # 최소 크기
    self.root.resizable(False, True)     # 가로는 고정, 세로만 조절 가능
    self.root.configure(bg=BG)

    self.load_data()   # 저장된 기록(시험일, 과목, 공부 시간)을 먼저 불러와요
    self.fill_colors() # 색이 아직 없는 과목에는 색을 하나씩 나눠줘요

    # 스톱워치 상태
    self.selected = self.subjects[0] if self.subjects else None  # 지금 고른 과목
    self.running = False      # 스톱워치가 돌아가는 중인지
    self.session_base = 0.0   # 이번 스톱워치에서 이미 쌓인 초
    self.seg_start = None     # 현재 구간 시작 시각 (monotonic)
    self.seg_subject = None   # 현재 구간의 과목
    self.seg_date = None      # 현재 구간의 날짜
    self.last_save = 0.0      # 마지막으로 자동 저장한 시각
    self.last_tick = 0.0      # 마지막 화면 갱신(tick) 시각 (절전 감지용)
    self.timer_job = None     # 예약해 둔 다음 tick 작업 (취소할 때 필요)

    # 오늘 기록 목록 화면 관리용
    self.row_widgets = {}        # {과목명: (막대, 시간글자)} 형태로 화면 부품 보관
    self.rendered_names = None   # 지금 화면에 그려진 과목 목록 (바뀌었는지 비교용)

    # 화면을 위에서 아래 순서대로 만들어요
    self.build_top()
    self.build_timer()
    self.build_subjects()
    self.build_buttons()
    self.build_records()

    # 화면 부품이 다 만들어진 뒤에 내용을 채워요
    self.build_chips()
    self.refresh_dday()
    self.update_status()
    self.render_records()
    self.auto_refresh()

  # ---------- 데이터 저장/불러오기 ----------
  def load_data(self):
    # 먼저 기본값을 세팅해 두고, 파일이 있으면 그 값으로 덮어써요.
    self.target_date = datetime.date(2026, 11, 19)  # 기본 시험일
    self.subjects = list(DEFAULT_SUBJECTS)  # list()로 복사본을 만들어 원본 보호
    self.records = {}  # {"2026-11-10": {"수학": 3600.0, ...}, ...}
    self.colors = {}   # {"수학": "#4f6df5", ...} 과목마다 고정된 색

    loaded = None
    # 새 파일 -> 예전 파일 순서로 시도. 먼저 성공한 파일을 쓰고 반복을 끝내요.
    for path in (DATA_FILE, LEGACY_FILE):
      try:
        with open(path, "r", encoding="utf-8") as f:
          loaded = json.load(f)
        break
      except OSError:      # 파일이 없거나 읽을 수 없는 경우
        continue           # 다음 파일로 넘어가요
      except ValueError:   # 파일은 있는데 내용(JSON)이 깨진 경우
        self.backup_broken(path)   # 다음 저장 때 덮어써서 날리지 않게 .bak으로 보관
        continue
    if not isinstance(loaded, dict):
      return   # 불러온 게 없으면 기본값 그대로 사용

    # 시험 날짜: 값이 없거나 형식이 이상하면 기본값을 유지
    try:
      self.target_date = datetime.date.fromisoformat(loaded["target_date"])
    except (KeyError, ValueError, TypeError):
      pass

    # 과목 목록: "문자열만 들어있는 리스트"일 때만 인정 (파일이 망가졌을 때 대비)
    subs = loaded.get("subjects")
    if isinstance(subs, list) and all(isinstance(s, str) for s in subs):
      self.subjects = subs

    # 과목별 색: 문자열끼리 짝지어진 것만 인정
    cols = loaded.get("colors")
    if isinstance(cols, dict):
      self.colors = {
          k: v for k, v in cols.items()
          if isinstance(k, str) and isinstance(v, str)
      }

    # 공부 기록: 날짜별 -> 과목별 초 단위 시간. 숫자인 값만 걸러서 가져와요.
    recs = loaded.get("records")
    if isinstance(recs, dict):
      for day, per in recs.items():
        if isinstance(per, dict):
          self.records[day] = {
              k: float(v) for k, v in per.items()
              if isinstance(k, str) and isinstance(v, (int, float))
          }

  def backup_broken(self, path):
    # 깨진 데이터 파일을 "이름.bak"으로 옮겨 둬요. (나중에 복구할 수 있도록)
    try:
      os.replace(path, path + ".bak")
    except OSError:
      pass

  def fill_colors(self):
    # 색이 아직 없는 과목에게, 다른 과목이 안 쓰는 색을 하나씩 나눠줘요.
    # 한 번 정해진 색은 저장되므로, 다른 과목을 지워도 색이 바뀌지 않아요.
    for name in self.subjects:
      if name not in self.colors:
        used = set(self.colors.values())
        free = [c for c in SUBJECT_COLORS if c not in used]
        if free:
          self.colors[name] = free[0]
        else:
          # 색을 다 썼으면 처음부터 다시 돌려 써요
          self.colors[name] = SUBJECT_COLORS[len(self.colors) % len(SUBJECT_COLORS)]

  def save_data(self):
    # 저장할 내용을 하나의 딕셔너리로 묶어요.
    payload = {
        "target_date": self.target_date.isoformat(),
        "subjects": self.subjects,
        "colors": self.colors,
        "records": {
            day: {k: round(v, 1) for k, v in per.items()}   # 소수점 첫째 자리까지만
            for day, per in self.records.items()
        },
    }
    # 안전하게 저장하는 방법: 임시 파일(.tmp)에 먼저 쓰고, 다 쓰면 원래 파일과 교체.
    # 이러면 저장 도중 꺼져도 기존 파일이 깨지지 않아요.
    tmp = DATA_FILE + ".tmp"
    try:
      with open(tmp, "w", encoding="utf-8") as f:
        # ensure_ascii=False: 한글이 \uXXXX 로 깨지지 않고 그대로 저장되게 함
        json.dump(payload, f, ensure_ascii=False, indent=1)
      os.replace(tmp, DATA_FILE)
    except OSError:
      pass  # 저장에 실패해도 프로그램은 계속 동작

  # ---------- 화면 만들기 ----------
  def build_top(self):
    # 맨 위: 제목, 시험일 글자, D-Day 배너, 시험 날짜 설정 버튼
    tk.Label(
        self.root, text="🎯 고교 공부 메이트", font=(FONT, 19, "bold"),
        bg=BG, fg=TEXT
    ).pack(pady=(22, 2))

    self.date_label = tk.Label(
        self.root, text="", font=(FONT, 10), bg=BG, fg=MUTED
    )
    self.date_label.pack()

    # D-Day 안내 (맨 위에 바로 보이는 배너)
    self.banner = tk.Label(
        self.root, text="", font=(FONT, 13, "bold"), bg=PRIMARY_SOFT,
        fg=PRIMARY, pady=11
    )
    self.banner.pack(fill="x", padx=28, pady=(10, 8))

    FlatButton(
        self.root, "📅 시험 날짜 설정", self.open_calendar, GRAY, TEXT,
        GRAY_HOVER, font=(FONT, 10, "bold"), padx=16, pady=6
    ).pack()

  def build_timer(self):
    # 큰 스톱워치 숫자와 그 아래 상태 표시(준비/공부 중/일시정지)
    self.timer_label = tk.Label(
        self.root, text="00:00:00", font=(FONT, 46, "bold"), bg=BG, fg=TEXT
    )
    self.timer_label.pack(pady=(16, 4))

    self.status_label = tk.Label(
        self.root, text="", font=(FONT, 10, "bold"), bg=GRAY, fg=MUTED,
        padx=12, pady=3
    )
    self.status_label.pack()

  def build_subjects(self):
    # 과목 선택 영역의 틀만 만들어요. 실제 과목 버튼은 build_chips()가 채워요.
    tk.Label(
        self.root, text="📚 공부할 과목", font=(FONT, 10, "bold"),
        bg=BG, fg=MUTED
    ).pack(anchor="w", padx=28, pady=(16, 4))

    self.chip_frame = tk.Frame(self.root, bg=BG)
    self.chip_frame.pack(fill="x", padx=25)
    # 한 줄에 4칸. uniform을 같은 이름으로 주면 모든 칸 너비가 똑같아져요.
    for col in range(4):
      self.chip_frame.columnconfigure(col, weight=1, uniform="chip")

    tk.Label(
        self.root, text="과목을 우클릭하면 삭제할 수 있어요",
        font=(FONT, 9), bg=BG, fg=MUTED
    ).pack(anchor="w", padx=28, pady=(2, 0))

  def build_buttons(self):
    # 시작 / 정지 / 리셋 버튼 3개를 한 줄에 나란히 배치
    row = tk.Frame(self.root, bg=BG)
    row.pack(fill="x", padx=24, pady=(14, 0))
    FlatButton(
        row, "▶  시작", self.start_timer, PRIMARY, "white", PRIMARY_HOVER,
        pady=11
    ).pack(side="left", expand=True, fill="x", padx=4)
    FlatButton(
        row, "⏸  정지", self.stop_timer, DANGER, "white", DANGER_HOVER,
        pady=11
    ).pack(side="left", expand=True, fill="x", padx=4)
    FlatButton(
        row, "↺  리셋", self.reset_timer, GRAY, TEXT, GRAY_HOVER, pady=11
    ).pack(side="left", expand=True, fill="x", padx=4)

  def build_records(self):
    # 아래쪽 "오늘 공부 기록" 영역의 틀 (구분선, 제목줄, 과목별 막대가 들어갈 자리)
    tk.Frame(self.root, bg=BORDER, height=1).pack(
        fill="x", padx=28, pady=(18, 10)
    )

    head = tk.Frame(self.root, bg=BG)
    head.pack(fill="x", padx=28)
    tk.Label(
        head, text="📊 오늘 공부 기록", font=(FONT, 10, "bold"),
        bg=BG, fg=MUTED
    ).pack(side="left")
    FlatButton(
        head, "지우기", self.clear_today, BG, MUTED, GRAY,
        font=(FONT, 9), padx=8, pady=2
    ).pack(side="right")
    self.total_label = tk.Label(
        head, text="총 00:00:00", font=(FONT, 11, "bold"), bg=BG, fg=TEXT
    )
    self.total_label.pack(side="right", padx=(0, 6))

    # 과목별 막대 그래프 줄들이 들어갈 상자 (render_records가 채워요)
    # 과목이 많아도 창 밖으로 넘치지 않게, 스크롤되는 영역(Canvas) 안에 넣어요.
    holder = tk.Frame(self.root, bg=BG)
    holder.pack(fill="both", expand=True, padx=28, pady=(8, 14))
    self.records_canvas = tk.Canvas(
        holder, bg=BG, highlightthickness=0, height=90, yscrollincrement=30
    )
    self.records_canvas.pack(fill="both", expand=True)
    self.rows_frame = tk.Frame(self.records_canvas, bg=BG)
    self.rows_window = self.records_canvas.create_window(
        (0, 0), window=self.rows_frame, anchor="nw"
    )
    # 내용 크기가 바뀌면 스크롤 범위를 다시 계산
    self.rows_frame.bind(
        "<Configure>",
        lambda e: self.records_canvas.configure(
            scrollregion=self.records_canvas.bbox("all")
        ),
    )
    # 창 너비가 바뀌면 내용 너비도 맞춰요
    self.records_canvas.bind(
        "<Configure>",
        lambda e: self.records_canvas.itemconfigure(self.rows_window, width=e.width),
    )
    # 마우스 휠(또는 터치패드 두 손가락 스크롤)로 목록을 넘길 수 있어요
    self.root.bind_all("<MouseWheel>", self.on_mousewheel)

  def on_mousewheel(self, event):
    # 목록이 보이는 영역보다 길 때만 스크롤해요.
    if self.rows_frame.winfo_reqheight() > self.records_canvas.winfo_height():
      self.records_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

  # ---------- 과목 칩 ----------
  # "칩" = 과목 이름이 적힌 작은 선택 버튼
  def color_for(self, name):
    # 과목마다 저장해 둔 고정 색을 써요. (삭제된 과목은 회색)
    if name in self.subjects:
      return self.colors.get(name, MUTED)
    return MUTED  # 삭제된 과목

  def build_chips(self):
    # 과목 버튼들을 지우고 처음부터 다시 만들어요. (과목 선택/추가/삭제 때 호출)
    for w in self.chip_frame.winfo_children():
      w.destroy()

    cols = 4   # 한 줄에 4개
    for i, name in enumerate(self.subjects):
      if name == self.selected:
        # 선택된 과목: 과목 고유 색으로 칠하고 흰 글씨
        color = self.color_for(name)
        bg, fg, hover = color, "white", color
      else:
        # 선택 안 된 과목: 회색
        bg, fg, hover = GRAY, TEXT, GRAY_HOVER
      chip = FlatButton(
          self.chip_frame, name, lambda n=name: self.select_subject(n),
          bg, fg, hover, font=(FONT, 10, "bold"), padx=6, pady=8
      )
      # i // cols = 몇 번째 줄, i % cols = 몇 번째 칸. 예) 5번째(i=5) -> 2줄 2칸
      chip.grid(row=i // cols, column=i % cols, padx=3, pady=3, sticky="ew")
      # 우클릭으로 삭제. Windows는 Button-3이 우클릭이에요.
      chip.bind("<Button-3>", lambda e, n=name: self.delete_subject(n))
      # Mac은 우클릭이 Button-2예요. Windows에서는 Button-2가 "휠 클릭"이라 Mac에서만 연결해요.
      if sys.platform == "darwin":
        chip.bind("<Button-2>", lambda e, n=name: self.delete_subject(n))

    # 맨 마지막 칸에는 "＋ 추가" 버튼을 놓아요.
    i = len(self.subjects)
    FlatButton(
        self.chip_frame, "＋ 추가", self.open_add_subject, PRIMARY_SOFT,
        PRIMARY, PRIMARY_SOFT_HOVER, font=(FONT, 10, "bold"), padx=6, pady=8
    ).grid(row=i // cols, column=i % cols, padx=3, pady=3, sticky="ew")

  def select_subject(self, name):
    # 과목 버튼을 눌렀을 때 실행돼요.
    if name == self.selected:
      return   # 이미 선택된 과목이면 할 일 없음
    if self.running:
      # 공부 중에 과목을 바꾸면 지금까지 시간을 이전 과목에 저장하고 이어서 측정
      self.commit_segment()
      self.seg_subject = name
    self.selected = name
    self.build_chips()      # 선택 색을 반영해서 버튼 다시 그림
    self.update_status()
    self.render_records()

  def open_add_subject(self):
    # 과목 추가 팝업을 열어요. 팝업이 "추가"를 누르면 self.add_subject가 호출돼요.
    AddSubjectDialog(self.root, self.add_subject)

  def add_subject(self, name):
    # 입력값 검사. 문제가 있으면 오류 문구를 return하고 (팝업이 보여줘요),
    # 문제가 없으면 과목을 추가한 뒤 None을 return해요.
    name = name.strip()   # 앞뒤 공백 제거
    if not name:
      return "과목 이름을 입력해 주세요."
    if len(name) > 8:
      return "이름은 8글자 이하로 해 주세요."
    if name in self.subjects:
      return "이미 있는 과목이에요."
    if len(self.subjects) >= MAX_SUBJECTS:
      return f"과목은 최대 {MAX_SUBJECTS}개까지 만들 수 있어요."
    self.subjects.append(name)
    self.fill_colors()          # 새 과목에 색 배정
    self.select_subject(name)   # 방금 추가한 과목을 바로 선택
    self.save_data()
    return None

  def delete_subject(self, name):
    # 정말 삭제할지 물어봐요. (예=True, 아니오=False)
    ok = messagebox.askyesno(
        "과목 삭제",
        f"'{name}' 과목을 삭제할까요?\n(지금까지의 기록은 그대로 남아요)",
        parent=self.root,
    )
    if not ok:
      return
    # 삭제하려는 과목을 지금 공부 중이면 먼저 정지(시간 저장)
    if self.running and self.seg_subject == name:
      self.stop_timer()
    self.subjects.remove(name)
    self.colors.pop(name, None)   # 그 과목의 색 정보도 삭제
    # 선택돼 있던 과목을 지웠다면 첫 번째 과목으로 바꿔요. (과목이 없으면 None)
    if self.selected == name:
      self.selected = self.subjects[0] if self.subjects else None
    self.save_data()
    self.build_chips()
    self.update_status()
    self.render_records()

  # ---------- 오늘 기록 목록 ----------
  def today_seconds(self):
    # 오늘 과목별 공부 시간(초)을 계산해요. {"수학": 3600.0, ...}
    today = today_iso()
    secs = dict(self.records.get(today, {}))   # dict()로 복사: 원본 기록을 건드리지 않으려고
    # 지금 스톱워치가 돌고 있다면, 아직 저장되지 않은 진행 중 시간도 더해서 보여줘요.
    if self.running and self.seg_date == today:
      live = time.monotonic() - self.seg_start
      secs[self.seg_subject] = secs.get(self.seg_subject, 0.0) + live
    return secs

  def rebuild_rows(self, names):
    # 과목별 막대 줄을 처음부터 다시 만들어요. (보여줄 과목 목록이 바뀔 때만 호출)
    for w in self.rows_frame.winfo_children():
      w.destroy()
    self.row_widgets = {}
    self.rendered_names = tuple(names)   # "지금 이 목록으로 그렸다"고 기억해 둠

    # 기록이 하나도 없으면 안내 문구만 보여줘요.
    if not names:
      tk.Label(
          self.rows_frame,
          text="아직 기록이 없어요. 과목을 고르고 시작을 눌러 보세요!",
          font=(FONT, 10), bg=BG, fg=MUTED
      ).pack(anchor="w", pady=4)
      return

    # 한 줄 구성: [과목 이름] [막대 그래프] [시간 글자]
    for name in names:
      row = tk.Frame(self.rows_frame, bg=BG)
      row.pack(fill="x", pady=3)
      row.columnconfigure(1, weight=1)   # 가운데(막대) 칸이 남는 공간을 모두 차지

      tk.Label(
          row, text=name, width=8, anchor="w", font=(FONT, 10, "bold"),
          bg=BG, fg=TEXT
      ).grid(row=0, column=0)

      # 막대: 회색 트랙(배경 틀) 위에 색깔 막대(fill)를 겹쳐서 놓아요.
      track = tk.Frame(row, bg=GRAY, height=10)
      track.grid(row=0, column=1, sticky="ew", padx=8)
      fill = tk.Frame(track, bg=self.color_for(name))
      # relwidth = 트랙 너비 대비 비율 (0.02 = 2%). 나중에 render_records가 갱신해요.
      fill.place(x=0, y=0, relheight=1, relwidth=0.02)

      time_label = tk.Label(
          row, text="00:00:00", width=9, anchor="e", font=(FONT, 10),
          bg=BG, fg=TEXT
      )
      time_label.grid(row=0, column=2)
      # 나중에 값만 바꿀 수 있게 막대와 시간 글자를 과목 이름으로 보관
      self.row_widgets[name] = (fill, time_label)

  def render_records(self):
    # 오늘 기록 영역을 최신 상태로 갱신해요. (타이머가 돌 때 0.2초마다 호출됨)
    secs = self.today_seconds()
    # 1초 이상 공부한 과목(또는 지금 공부 중인 과목)만 목록에 표시
    names = [
        s for s in self.subjects
        if secs.get(s, 0) >= 1 or (self.running and s == self.seg_subject)
    ]
    # 이미 삭제된 과목이라도 오늘 기록이 있으면 뒤에 같이 표시
    names += [s for s in secs if s not in self.subjects and secs[s] >= 1]

    self.total_label.config(text=f"총 {fmt_hms(sum(secs.values()))}")

    # 표시할 과목 목록이 바뀐 경우에만 줄을 새로 만들어요. (매번 새로 만들면 깜빡임/낭비)
    if tuple(names) != self.rendered_names:
      self.rebuild_rows(names)

    # 가장 오래 공부한 과목을 100% 기준으로 삼아 막대 길이를 정해요.
    # [... ] + [1] 은 목록이 비었을 때 max()가 오류 나지 않게 하고, 0으로 나누기도 막아요.
    biggest = max([secs.get(n, 0) for n in names] + [1])
    for n in names:
      fill, time_label = self.row_widgets[n]
      value = secs.get(n, 0)
      fill.place_configure(relwidth=max(value / biggest, 0.02))   # 최소 2%는 보이게
      time_label.config(text=fmt_hms(value))

  def clear_today(self):
    # "지우기" 버튼: 오늘 기록을 전부 삭제
    today = today_iso()
    # 지울 기록도 없고 공부 중도 아니면 아무것도 안 해요.
    if not self.records.get(today) and not self.running:
      return
    ok = messagebox.askyesno(
        "기록 지우기", "오늘 공부 기록을 모두 지울까요?", parent=self.root
    )
    if not ok:
      return
    self.records.pop(today, None)   # 오늘 기록 삭제 (없어도 오류 안 나게 None 지정)
    if self.running:
      self.seg_start = time.monotonic()  # 지금까지 진행분도 같이 지움
    self.session_base = 0.0   # 위쪽 스톱워치 숫자도 0으로 맞춰서 기록과 어긋나지 않게
    self.save_data()
    self.show_time()
    self.update_status()
    self.render_records()

  # ---------- D-Day ----------
  def refresh_dday(self):
    # 시험일 글자와 D-Day 배너를 갱신해요.
    days = days_until(self.target_date)
    self.date_label.config(text=f"시험일: {format_date_kr(self.target_date)}")
    if days <= DDAY_WARN_DAYS:  # 며칠 안 남았으면 빨간색으로 강조
      bg, fg = DANGER_SOFT, DANGER
    else:
      bg, fg = PRIMARY_SOFT, PRIMARY
    self.banner.config(text=make_banner_text(self.target_date), bg=bg, fg=fg)

  def auto_refresh(self):
    # 켜 둔 채 자정이 지나도 반영되도록 1분마다 갱신
    self.refresh_dday()
    self.render_records()
    # after(60000, ...) = 60000ms(1분) 뒤에 이 함수를 다시 실행 (스스로 반복 예약)
    self.root.after(AUTO_REFRESH_MS, self.auto_refresh)

  def open_calendar(self):
    # 달력 팝업을 열어요. "설정 완료"를 누르면 self.set_target_date가 호출돼요.
    CalendarPopup(self.root, self.target_date, self.set_target_date)

  def set_target_date(self, new_date):
    self.target_date = new_date
    self.save_data()
    self.refresh_dday()

  # ---------- 스톱워치 ----------
  # 핵심 개념: 공부 시간은 "구간(segment)" 단위로 쌓아요.
  #  - session_base : 이번 스톱워치에서 이미 확정된(더해진) 초
  #  - seg_start    : 지금 진행 중인 구간이 시작된 시각
  #  - 화면에 보이는 시간 = session_base + (지금 - seg_start)
  # 과목을 바꾸거나 30초가 지나면 현재 구간을 기록에 더하고(commit) 새 구간을 시작해요.
  def current_elapsed(self):
    # 지금 화면에 보여줄 스톱워치 시간(초)
    if self.running:
      return self.session_base + (time.monotonic() - self.seg_start)
    return self.session_base

  def show_time(self):
    self.timer_label.config(text=fmt_hms(self.current_elapsed()))

  def update_status(self):
    # 상태 표시: 공부 중 / 일시정지 / 준비
    if self.running:
      self.status_label.config(
          text=f"● {self.seg_subject} 공부 중", bg=SUCCESS_SOFT, fg=SUCCESS
      )
    elif self.session_base > 0:
      self.status_label.config(text="● 일시정지", bg=WARN_SOFT, fg=WARN)
    else:
      self.status_label.config(text="● 준비", bg=GRAY, fg=MUTED)

  def commit_segment(self):
    """지금까지 흐른 시간을 현재 과목 기록에 더하고, 구간을 새로 시작한다."""
    if not self.running or self.seg_start is None:
      return   # 돌고 있지 않으면 저장할 게 없음
    now = time.monotonic()
    delta = now - self.seg_start   # 이번 구간에서 흐른 시간(초)
    # setdefault: 그 날짜 기록이 없으면 빈 딕셔너리를 만들어서 가져와요.
    per_day = self.records.setdefault(self.seg_date, {})
    per_day[self.seg_subject] = per_day.get(self.seg_subject, 0.0) + delta
    self.session_base += delta   # 위쪽 큰 스톱워치 숫자에도 반영
    self.seg_start = now         # 새 구간은 지금부터 시작
    self.seg_date = today_iso()  # 자정을 넘겼다면 새 날짜로 바꿔줌

  def tick(self):
    # 스톱워치가 돌아가는 동안 0.2초마다 반복 실행되는 함수
    now = time.monotonic()
    gap = now - self.last_tick   # 지난 tick 이후 흐른 시간 (평소엔 약 0.2초)
    if self.running and gap > SLEEP_GAP_SECONDS:
      # 노트북 덮개를 닫는 등 절전 상태였다가 돌아온 경우예요.
      # 그 공백만큼 구간 시작 시각을 뒤로 밀어서, 잠든 시간은 공부 시간에서 빼요.
      self.seg_start = min(self.seg_start + gap, now)
    self.last_tick = now
    self.show_time()
    if self.running and now - self.last_save >= AUTOSAVE_SECONDS:
      # 일정 시간마다 자동 저장 (갑자기 꺼져도 기록이 남도록)
      self.commit_segment()
      self.save_data()
      self.last_save = now
    self.render_records()
    if self.running:
      # TICK_MS 뒤에 tick을 다시 실행하도록 예약. 반환된 작업 번호는 취소할 때 써요.
      self.timer_job = self.root.after(TICK_MS, self.tick)

  def cancel_timer_job(self):
    # 예약된 tick이 있으면 취소해요. (중복 실행 방지)
    if self.timer_job is not None:
      self.root.after_cancel(self.timer_job)
      self.timer_job = None

  def start_timer(self):
    if self.running:
      return   # 이미 돌고 있으면 무시 (시작 버튼 연타 방지)
    if not self.selected:
      messagebox.showinfo(
          "과목 없음", "먼저 ＋ 추가 버튼으로 과목을 추가해 주세요!",
          parent=self.root
      )
      return
    self.running = True
    # 새 구간 시작: 어떤 과목을, 어느 날짜에, 언제부터 공부하는지 기록
    self.seg_subject = self.selected
    self.seg_date = today_iso()
    self.seg_start = time.monotonic()
    self.last_save = self.seg_start
    self.last_tick = self.seg_start   # 절전 감지 기준점
    self.update_status()
    self.cancel_timer_job()
    self.tick()   # tick을 처음 한 번 실행하면, 이후엔 tick이 스스로 반복 예약해요.

  def stop_timer(self):
    if not self.running:
      return
    self.commit_segment()   # 마지막 구간까지 기록에 더함
    self.running = False
    self.seg_start = None
    self.cancel_timer_job()
    self.save_data()
    self.show_time()
    self.update_status()
    self.render_records()

  def reset_timer(self):
    # 위쪽 스톱워치 숫자만 0으로 되돌려요 (저장된 과목별 기록은 그대로)
    self.stop_timer()
    self.session_base = 0.0
    self.show_time()
    self.update_status()

  def on_close(self):
    # 창의 X 버튼을 눌렀을 때: 돌고 있는 타이머를 멈추고 저장한 뒤 종료
    self.stop_timer()
    self.save_data()
    self.root.destroy()


# 이 파일을 직접 실행했을 때만 아래가 동작해요. (다른 파일에서 import하면 실행 안 됨)
if __name__ == "__main__":
  root = tk.Tk()          # 메인 창 만들기
  app = StudyApp(root)    # 앱 화면 구성
  # X 버튼을 누르면 그냥 닫지 않고 app.on_close를 먼저 실행하도록 연결
  root.protocol("WM_DELETE_WINDOW", app.on_close)

  # 실행할 때마다 창을 맨 앞으로 가져오기 (VS Code 뒤에 숨는 문제 방지)
  root.lift()
  root.attributes("-topmost", True)                          # 잠깐 항상 위로 올렸다가
  root.after(300, lambda: root.attributes("-topmost", False))  # 0.3초 뒤에 해제
  root.focus_force()

  root.mainloop()   # 창을 계속 띄워 두고 클릭/키 입력을 기다리는 "메인 루프"
