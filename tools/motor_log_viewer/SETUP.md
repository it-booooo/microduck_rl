# 第一次設定環境指南

這份指南是給**第一次要在自己電腦上跑 Motor Log Viewer** 的人看的——目標是照著做,
10 分鐘內看到視窗跳出來、載入一份 `logs/*.csv` 成功。架構說明、功能介紹請看
[README.md](README.md),這份只管「怎麼讓它動起來」。

適用環境:Linux(Ubuntu)+ 桌面環境(要能顯示視窗)。

---

## 步驟 0:確認你在 repo 根目錄

所有指令都要在 `microduck_rl` 這個資料夾底下執行(不是它的上層、也不是
`tools/motor_log_viewer/` 裡面):

```bash
cd ~/projects/microduck_rl
ls pyproject.toml tools/motor_log_viewer   # 兩個都要存在
```

## 步驟 1:裝系統套件(只需要做一次)

這個工具用 PySide6(Qt)畫視窗,Linux 上 Qt 需要一個系統函式庫才能開視窗,
大部分乾淨安裝的 Ubuntu 都沒有預先裝好:

```bash
sudo apt install libxcb-cursor0
```

**怎麼知道自己是不是已經裝過**:如果之後執行工具時跳出

```
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" ...
Aborted (core dumped)
```

代表還沒裝,回來裝這個套件就會解決。

## 步驟 2:選一種方式安裝 Python 套件

這個工具需要 **PySide6、pandas、matplotlib、numpy**,但這些**不是**
`microduck_rl` 主專案(RL 訓練用)的相依套件,所以不會在 `uv sync` 時自動裝好。
兩種方式擇一即可,效果一樣:

### 方式 A:`uv run --with ...`(推薦,不留下任何東西)

不用安裝、不用啟用任何環境,每次執行指令時用 `--with` 臨時帶上需要的套件:

```bash
uv run --with PySide6 --with pandas python -m tools.motor_log_viewer logs/walk_vx0.20.csv
```

第一次執行會花點時間下載 PySide6(約 250 MB),之後會被 uv 快取,下次就很快。

### 方式 B:獨立的 conda 環境(裝一次、之後直接用)

如果你習慣用 conda、或不想每次打一長串 `--with`,可以建一個專門給這個工具用的
conda 環境(**跟 RL 訓練用的 `.venv` 是分開的,互不影響**):

```bash
conda create -n env_microduck python=3.11 -y
conda activate env_microduck
python -m pip install PySide6 pandas matplotlib numpy
```

之後每次只要:

```bash
conda activate env_microduck
cd ~/projects/microduck_rl
python -m tools.motor_log_viewer logs/walk_vx0.20.csv
```

> **這個 conda 環境只用來跑 GUI 分析工具**,沒有裝 mjlab、torch、bam 等 RL 訓練用的套件。
> 訓練/匯出/發布策略(`uv run train`、`uv run play` 等,見 [AGENTS.md](../../AGENTS.md))
> 一律還是用 `uv run`,不要用這個 conda 環境跑。

## 步驟 3:驗證裝好了

跑這行,應該要跳出視窗,標題列顯示 `walk_vx0.20.csv - Microduck Motor Log Viewer`:

```bash
# 方式 A
uv run --with PySide6 --with pandas python -m tools.motor_log_viewer logs/walk_vx0.20.csv

# 方式 B(已 conda activate env_microduck)
python -m tools.motor_log_viewer logs/walk_vx0.20.csv
```

左側會看到 14 顆馬達依 RMS 轉矩排序的表格,右上是可勾選關節的時序圖,
右下是可下拉切換關節的轉矩–轉速圖。能看到這些就代表裝好了。

沒有現成的 `logs/*.csv` 可以開?看下一節。

## 步驟 4(選用):自己產生一份記錄檔案

Motor Log Viewer 只負責「看」CSV,不負責「產生」CSV——CSV 是另一支腳本
[scripts/log_motor_data.py](../../scripts/log_motor_data.py) 用 walking 策略跑模擬產生的,
那支腳本走的是 `uv run`(不是 conda),因為它需要 mjlab/torch/bam 等訓練套件:

```bash
uv run scripts/log_motor_data.py --walking policies/velstand.onnx --new-cmd-obs \
    --lin-vel-x 0.2 --duration 12 --out logs/walk_vx0.20.csv
```

產生後,原本開 Motor Log Viewer 的指令直接指到新檔案就能看了。

---

## 疑難排解

| 看到的錯誤 | 原因 | 怎麼解 |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'PySide6'` | 忘了帶 `--with PySide6`,或 conda 環境裡沒裝 | 方式 A 補上 `--with PySide6`;方式 B 先 `conda activate env_microduck` 再執行,必要時重新 `pip install` |
| `ImportError: attempted relative import with no known parent package` | 用 `python 路徑/__main__.py` 直接執行檔案(例如編輯器的「執行目前檔案」按鈕) | 改用 `python -m tools.motor_log_viewer ...`,不要直接指路徑執行 |
| `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"` / `Aborted (core dumped)` | 系統缺 Qt 用的 `libxcb-cursor0` | 回到步驟 1:`sudo apt install libxcb-cursor0` |
| 指令找不到 `tools` 這個模組 / `No module named 'tools'` | 目前工作目錄不是 repo 根目錄 | `cd ~/projects/microduck_rl` 再執行 |
| 開啟 CSV 後跳出「Motor Log Validation」警告 | CSV 的欄位或數值有問題(例如手動編輯過、記錄中途跌倒) | 讀警告訊息裡的細節(會附一份 `*.check.csv` 報告),確認後可選擇「Load anyway」繼續載入 |
| 表格的 `Peak V`、`V sat [%]` 都顯示 `nan` | 這份 CSV 的 `.meta.json` 是這個電壓功能加入前產生的,沒有 `R_ohm`/`vin_V` | 用步驟 4 的指令重新產生一份新的 CSV,新版 `log_motor_data.py` 會自動記錄這些欄位 |

## 下一步

- 想了解這個工具的程式架構(為什麼分成 `data/`、`application/`、`ui/` 這些資料夾)→ 看 [README.md](README.md)
- 想了解 `V sat` / `At limit` 這些欄位代表什麼物理意義 → 看 README 或問 Claude
- 想跑完整的 RL 訓練流程(不是這個分析工具)→ 看 repo 根目錄的 [AGENTS.md](../../AGENTS.md)
