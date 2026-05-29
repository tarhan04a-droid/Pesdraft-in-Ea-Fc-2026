import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import pandas as pd
import time
import requests
from io import BytesIO
from PIL import Image, ImageTk
import random

# Global Variables
df = None
p1_full_list = []
p2_full_list = []
all_options = []
max_rounds = 1
current_round = 1

# --- HARDCODED EA FC FORMATIONS ---
FORMATIONS = {
    "4-3-3 Attack": ['GK', 'RB', 'CB', 'CB', 'LB', 'CM', 'CM', 'CAM', 'RW', 'LW', 'ST'],
    "4-3-3 Defend": ['GK', 'RB', 'CB', 'CB', 'LB', 'CDM', 'CDM', 'CM', 'RW', 'LW', 'ST'],
    "4-3-3 Holding": ['GK', 'RB', 'CB', 'CB', 'LB', 'CDM', 'CM', 'CM', 'RW', 'LW', 'ST'],
    "4-3-3 False 9": ['GK', 'RB', 'CB', 'CB', 'LB', 'CDM', 'CM', 'CM', 'RW', 'LW', 'CF'],
    "4-4-2 Flat": ['GK', 'RB', 'CB', 'CB', 'LB', 'RM', 'CM', 'CM', 'LM', 'ST', 'ST'],
    "4-4-2 Holding": ['GK', 'RB', 'CB', 'CB', 'LB', 'RM', 'CDM', 'CDM', 'LM', 'ST', 'ST'],
    "4-2-3-1 Wide": ['GK', 'RB', 'CB', 'CB', 'LB', 'CDM', 'CDM', 'RM', 'LM', 'CAM', 'ST'],
    "4-2-3-1 Narrow": ['GK', 'RB', 'CB', 'CB', 'LB', 'CDM', 'CDM', 'CAM', 'CAM', 'CAM', 'ST'],
    "4-1-2-1-2 Wide": ['GK', 'RB', 'CB', 'CB', 'LB', 'CDM', 'RM', 'LM', 'CAM', 'ST', 'ST'],
    "4-1-2-1-2 Narrow": ['GK', 'RB', 'CB', 'CB', 'LB', 'CDM', 'CM', 'CM', 'CAM', 'ST', 'ST'],
    "4-3-2-1 (Christmas Tree)": ['GK', 'RB', 'CB', 'CB', 'LB', 'CM', 'CM', 'CM', 'CF', 'CF', 'ST'],
    "4-5-1 Flat": ['GK', 'RB', 'CB', 'CB', 'LB', 'RM', 'CM', 'CM', 'CM', 'LM', 'ST'],
    "4-5-1 Attack": ['GK', 'RB', 'CB', 'CB', 'LB', 'RM', 'CM', 'CAM', 'CAM', 'LM', 'ST'],
    "3-5-2": ['GK', 'CB', 'CB', 'CB', 'CDM', 'CDM', 'RM', 'LM', 'CAM', 'ST', 'ST'],
    "3-4-1-2": ['GK', 'CB', 'CB', 'CB', 'CM', 'CM', 'RM', 'LM', 'CAM', 'ST', 'ST'],
    "3-4-2-1": ['GK', 'CB', 'CB', 'CB', 'CM', 'CM', 'RM', 'LM', 'CF', 'CF', 'ST'],
    "5-3-2": ['GK', 'RWB', 'CB', 'CB', 'CB', 'LWB', 'CM', 'CM', 'CM', 'ST', 'ST'],
    "5-2-1-2": ['GK', 'RWB', 'CB', 'CB', 'CB', 'LWB', 'CM', 'CM', 'CAM', 'ST', 'ST'],
    "5-4-1 Flat": ['GK', 'RWB', 'CB', 'CB', 'CB', 'LWB', 'RM', 'CM', 'CM', 'LM', 'ST']
}

# Global GUI Widgets
window = None
status_label = None
lbl_left, lbl_right, list_left, list_right = None, None, None, None
lbl_photo, lbl_photo_name = None, None
cb_trade_rounds = None
btn_trade = None
o1, o2 = None, None
p1_t1, p1_t2, p1_t3, p1_t4 = None, None, None, None
p2_t1, p2_t2, p2_t3, p2_t4 = None, None, None, None
cb_p1_form, cb_p2_form = None, None


def select_csv():
    global df, all_options
    file_path = filedialog.askopenfilename(title="Select FC26 Players CSV", filetypes=[("CSV Files", "*.csv")])
    if file_path:
        try:
            df = pd.read_csv(file_path, encoding="utf-8-sig", low_memory=False)
        except:
            df = pd.read_csv(file_path, encoding="latin-1", low_memory=False)
                
        options = set()
        if "club_name" in df.columns: options.update(df["club_name"].dropna().unique())
        if "league_name" in df.columns: options.update(df["league_name"].dropna().unique())
        if "nationality_name" in df.columns: options.update(df["nationality_name"].dropna().unique())
        
        all_options = sorted(list(options))
        for cb in [p1_t1, p1_t2, p1_t3, p1_t4, p2_t1, p2_t2, p2_t3, p2_t4]: cb['values'] = all_options
        status_label.config(text=f"✅ Players loaded! {len(all_options)} options available.", fg="#00ff00")
    else:
        status_label.config(text="⚠️ No file selected!", fg="orange")


def get_photo(url):
    try:
        if pd.isna(url) or str(url).strip() == "": return None
        response = requests.get(url, timeout=2)
        img = Image.open(BytesIO(response.content))
        return ImageTk.PhotoImage(img.resize((130, 130), Image.Resampling.LANCZOS))
    except: return None


def guarantee_formation(selected_df, pool_df, formation_positions):
    flexibility = {
        'GK': ['GK'], 'CB': ['CB', 'LCB', 'RCB'], 'LB': ['LB', 'LWB'], 'RB': ['RB', 'RWB'],
        'CM': ['CM', 'LCM', 'RCM', 'CDM'], 'CAM': ['CAM', 'CM', 'CF'], 'LW': ['LW', 'LM'],
        'RW': ['RW', 'RM'], 'ST': ['ST', 'CF'], 'RM': ['RM', 'RW'], 'LM': ['LM', 'LW'],
        'CDM': ['CDM', 'CM'], 'RWB': ['RWB', 'RB'], 'LWB': ['LWB', 'LB']
    }
    current_squad = selected_df.copy(); used_indexes = set(); missing = []
    for need in formation_positions:
        accepted = flexibility.get(need, [need]); found = False
        availables = current_squad[~current_squad.index.isin(used_indexes)]
        for idx, row in availables.sort_values("overall", ascending=False).iterrows():
            positions = [p.strip() for p in str(row.get("player_positions", row.get("club_position", ""))).split(',')]
            if any(p in accepted for p in positions):
                used_indexes.add(idx); found = True; break
        if not found: missing.append(need)
    if missing:
        for m in missing:
            valid_pool = pool_df[(~pool_df.index.isin(current_squad.index)) & (pool_df['player_positions'].apply(lambda x: any(p.strip() in flexibility.get(m, [m]) for p in str(x).split(','))))]
            if not valid_pool.empty:
                new_player = valid_pool.sort_values("overall", ascending=False).head(1)
                empties = current_squad[~current_squad.index.isin(used_indexes)]
                if not empties.empty:
                    current_squad = pd.concat([current_squad.drop(empties.sort_values("overall").index[0]), new_player])
                    used_indexes.add(new_player.index[0])
    return current_squad


def get_24_fair(inputs, exclude_names, formation):
    selected = pd.DataFrame(); pool_df = pd.DataFrame()
    valid_inputs = [str(g).strip() for g in inputs if str(g).strip() != ""]
    if not valid_inputs: return []
    for t in valid_inputs:
        mask = pd.Series(False, index=df.index)
        if "club_name" in df.columns: mask |= df["club_name"].str.contains(t, case=False, na=False)
        if "league_name" in df.columns: mask |= df["league_name"].str.contains(t, case=False, na=False)
        if "nationality_name" in df.columns: mask |= df["nationality_name"].str.contains(t, case=False, na=False)
        t_df = df[mask & (~df['short_name'].isin(exclude_names))].sort_values("overall", ascending=False)
        selected = pd.concat([selected, t_df.head(6)]); pool_df = pd.concat([pool_df, t_df])
        pool_df = pool_df[(pool_df['overall'] <= 99) & (pool_df['overall'] > 0)]
    selected = selected[(selected['overall'] <= 99) & (selected['overall'] > 0)]
    selected = selected.drop_duplicates(subset=["short_name", "overall"])
    pool_df = pool_df.drop_duplicates(subset=["short_name", "overall"])
    if len(selected) < 24:
        selected = pd.concat([selected, pool_df[~pool_df['short_name'].isin(selected['short_name'])].sort_values("overall", ascending=False).head(24 - len(selected))])
    selected = guarantee_formation(selected.head(24), pool_df, formation).sort_values("overall", ascending=False)
    cards = []
    for i in range(len(selected)):
        player = selected.iloc[i]
        tier = "TOP" if i < 7 else "PRO" if i < 15 else "SUB" if i < 21 else "RES"
        cards.append({"name": str(player.get("short_name", "Unknown")), "ovr": int(player.get("overall", 0)), "pos": str(player.get("player_positions", "UNK")).split(',')[0], "photo": str(player.get("player_face_url", "")), "tier": tier})
    return sorted(cards, key=lambda x: x["ovr"])


def start_draft():
    global p1_full_list, p2_full_list, max_rounds, current_round
    if df is None: return messagebox.showerror("Error", "Select Players CSV first!")
    
    max_rounds, current_round = int(cb_trade_rounds.get()), 1
    p1_form, p2_form = FORMATIONS[cb_p1_form.get()], FORMATIONS[cb_p2_form.get()]
    lbl_left.config(text=f"{o1.get()} ({cb_p1_form.get()})"); lbl_right.config(text=f"{o2.get()} ({cb_p2_form.get()})")

    i1, i2 = [p1_t1.get(), p1_t2.get(), p1_t3.get(), p1_t4.get()], [p2_t1.get(), p2_t2.get(), p2_t3.get(), p2_t4.get()]
    if random.choice([True, False]):
        p1_cards = get_24_fair(i1, [], p1_form)
        p2_cards = get_24_fair(i2, [k['name'] for k in p1_cards], p2_form)
    else:
        p2_cards = get_24_fair(i2, [], p2_form)
        p1_cards = get_24_fair(i1, [k['name'] for k in p2_cards], p1_form)

    list_left.delete(0, tk.END); list_right.delete(0, tk.END)
    status_label.config(text="✅ Drafting...", fg="#00ff00"); btn_trade.config(state=tk.DISABLED)
    p1_full_list.clear(); p2_full_list.clear(); window.update()
    
    total_turns = max(len(p1_cards), len(p2_cards))
    for i in range(total_turns):
        wait_time = 0.05 + ((i / total_turns) ** 3) * 1.5 
        if i < len(p1_cards):
            c = p1_cards[i]; text = f"[{c['tier']}] [{c['pos']}] {c['name']} | OVR: {c['ovr']}"
            list_left.insert(tk.END, text); list_left.yview(tk.END); p1_full_list.append(text)
            photo = get_photo(c['photo'])
            if photo: lbl_photo.config(image=photo); lbl_photo.image = photo; lbl_photo_name.config(text=f"{c['name']} ({c['ovr']})", fg="#2196F3")
            window.update(); time.sleep(wait_time / 2)
        if i < len(p2_cards):
            c = p2_cards[i]; text = f"[{c['tier']}] [{c['pos']}] {c['name']} | OVR: {c['ovr']}"
            list_right.insert(tk.END, text); list_right.yview(tk.END); p2_full_list.append(text)
            photo = get_photo(c['photo'])
            if photo: lbl_photo.config(image=photo); lbl_photo.image = photo; lbl_photo_name.config(text=f"{c['name']} ({c['ovr']})", fg="#f44336")
            window.update(); time.sleep(wait_time / 2)
            
    p1_full_list.sort(key=lambda x: int(x.split("OVR: ")[1]), reverse=True)
    p2_full_list.sort(key=lambda x: int(x.split("OVR: ")[1]), reverse=True)
    list_left.delete(0, tk.END); list_right.delete(0, tk.END)
    for k in p1_full_list: list_left.insert(tk.END, k)
    for k in p2_full_list: list_right.insert(tk.END, k)
    status_label.config(text=f"🔥 DRAFT COMPLETED! ({max_rounds} Trade Rounds Left)", fg="#FFD700"); btn_trade.config(state=tk.NORMAL)


def open_final_screen(tw):
    tw.destroy(); btn_trade.config(state=tk.DISABLED)
    final_win = tk.Toplevel(window); final_win.title("🔥 FINAL SQUADS 🔥"); final_win.geometry("900x700"); final_win.configure(bg="#000000")
    tk.Label(final_win, text="🏆 DRAFT COMPLETED - FINAL SQUADS 🏆", font=("Arial", 20, "bold"), bg="#000000", fg="#FFD700").pack(pady=20)
    frame_lists = tk.Frame(final_win, bg="#000000"); frame_lists.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    f_p1 = tk.Frame(frame_lists, bg="#000000"); f_p1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tk.Label(f_p1, text=f"{o1.get()} SQUAD", font=("Arial", 16, "bold"), bg="#000000", fg="#2196F3").pack(pady=10)
    lb_p1 = tk.Listbox(f_p1, bg="#121212", fg="#2196F3", font=("Consolas", 12)); lb_p1.pack(fill=tk.BOTH, expand=True)
    for k in p1_full_list: lb_p1.insert(tk.END, k)

    f_p2 = tk.Frame(frame_lists, bg="#000000"); f_p2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    tk.Label(f_p2, text=f"{o2.get()} SQUAD", font=("Arial", 16, "bold"), bg="#000000", fg="#f44336").pack(pady=10)
    lb_p2 = tk.Listbox(f_p2, bg="#121212", fg="#f44336", font=("Consolas", 12)); lb_p2.pack(fill=tk.BOTH, expand=True)
    for k in p2_full_list: lb_p2.insert(tk.END, k)


def open_trade_room():
    tw = tk.Toplevel(window); tw.title("🔪 Blind Trade Room"); tw.geometry("600x600"); tw.configure(bg="#1e1e1e")
    trade_data = {"p1_protect": "", "p1_bait": "", "p1_target": "", "p2_protect": "", "p2_bait": "", "p2_target": ""}
    header = tk.Label(tw, text=f"🔄 TRADE ROUND: {current_round} / {max_rounds}", font=("Arial", 16, "bold"), fg="#FF9800", bg="#1e1e1e"); header.pack(pady=10)
    container = tk.Frame(tw, bg="#1e1e1e"); container.pack(fill=tk.BOTH, expand=True)

    def process_p1():
        if not cb_p1_prot.get() or not cb_p1_bait.get() or not cb_p1_targ.get(): return messagebox.showwarning("Error", "Fill all fields!")
        trade_data["p1_protect"], trade_data["p1_bait"], trade_data["p1_target"] = cb_p1_prot.get(), cb_p1_bait.get(), cb_p1_targ.get(); draw_p2_screen()

    def process_p2():
        if not cb_p2_prot.get() or not cb_p2_bait.get() or not cb_p2_targ.get(): return messagebox.showwarning("Error", "Fill all fields!")
        trade_data["p2_protect"], trade_data["p2_bait"], trade_data["p2_target"] = cb_p2_prot.get(), cb_p2_bait.get(), cb_p2_targ.get(); calculate_results(tw, container, trade_data, header)

    def draw_p1_screen():
        for w in container.winfo_children(): w.destroy()
        tk.Label(container, text=o1.get() + ", Your Turn!", font=("Arial", 14, "bold"), fg="#2196F3", bg="#1e1e1e").pack(pady=10)
        global cb_p1_prot, cb_p1_bait, cb_p1_targ
        tk.Label(container, text="Star to Protect:", fg="white", bg="#1e1e1e").pack(); cb_p1_prot = ttk.Combobox(container, values=p1_full_list, width=45, state="readonly"); cb_p1_prot.pack(pady=5)
        tk.Label(container, text="Bait to Sacrifice:", fg="white", bg="#1e1e1e").pack(); cb_p1_bait = ttk.Combobox(container, values=p1_full_list, width=45, state="readonly"); cb_p1_bait.pack(pady=5)
        tk.Label(container, text="Target to Steal:", fg="white", bg="#1e1e1e").pack(); cb_p1_targ = ttk.Combobox(container, values=p2_full_list, width=45, state="readonly"); cb_p1_targ.pack(pady=5)
        tk.Button(container, text="🔒 Lock Choices", bg="#2196F3", fg="white", font=("Arial", 11, "bold"), command=process_p1).pack(pady=20)

    def draw_p2_screen():
        for w in container.winfo_children(): w.destroy()
        tk.Label(container, text=o2.get() + ", Your Turn!", font=("Arial", 14, "bold"), fg="#f44336", bg="#1e1e1e").pack(pady=10)
        global cb_p2_prot, cb_p2_bait, cb_p2_targ
        tk.Label(container, text="Star to Protect:", fg="white", bg="#1e1e1e").pack(); cb_p2_prot = ttk.Combobox(container, values=p2_full_list, width=45, state="readonly"); cb_p2_prot.pack(pady=5)
        tk.Label(container, text="Bait to Sacrifice:", fg="white", bg="#1e1e1e").pack(); cb_p2_bait = ttk.Combobox(container, values=p2_full_list, width=45, state="readonly"); cb_p2_bait.pack(pady=5)
        tk.Label(container, text="Target to Steal:", fg="white", bg="#1e1e1e").pack(); cb_p2_targ = ttk.Combobox(container, values=p1_full_list, width=45, state="readonly"); cb_p2_targ.pack(pady=5)
        tk.Button(container, text="🔥 Start the Clash!", bg="#f44336", fg="white", font=("Arial", 11, "bold"), command=process_p2).pack(pady=20)

    def calculate_results(tw, container, t_data, header):
        global current_round, p1_full_list, p2_full_list
        for w in container.winfo_children(): w.destroy()
        new_p1 = p1_full_list.copy(); new_p2 = p2_full_list.copy()
        tk.Label(container, text="⚔️ BATTLE RESULTS ⚔️", font=("Arial", 16, "bold"), fg="white", bg="#1e1e1e").pack(pady=10)
        
        tgt1 = t_data["p1_target"] if t_data["p1_target"] != t_data["p2_protect"] else t_data["p2_bait"]
        bt1 = t_data["p1_bait"]
        if bt1 in new_p1 and tgt1 in new_p2:
            new_p1.remove(bt1); new_p2.remove(tgt1); new_p1.append(tgt1); new_p2.append(bt1)
            t1, c1 = (f"✅ {o1.get()} SUCCESS! \n{tgt1} stolen.", "#00ff00") if t_data["p1_target"] != t_data["p2_protect"] else (f"🛡️ {o1.get()} BLOCKED!", "orange")
        else: t1, c1 = f"⚠️ {o1.get()} CANCELLED!", "gray"
        tk.Label(container, text=t1, fg=c1, bg="#1e1e1e", font=("Arial", 11, "bold")).pack(pady=10)

        tgt2 = t_data["p2_target"] if t_data["p2_target"] != t_data["p1_protect"] else t_data["p1_bait"]
        bt2 = t_data["p2_bait"]
        if bt2 in new_p2 and tgt2 in new_p1:
            new_p2.remove(bt2); new_p1.remove(tgt2); new_p2.append(tgt2); new_p1.append(bt2)
            t2, c2 = (f"✅ {o2.get()} SUCCESS! \n{tgt2} stolen.", "#00ff00") if t_data["p2_target"] != t_data["p1_protect"] else (f"🛡️ {o2.get()} BLOCKED!", "orange")
        else: t2, c2 = f"⚠️ {o2.get()} CANCELLED!", "gray"
        tk.Label(container, text=t2, fg=c2, bg="#1e1e1e", font=("Arial", 11, "bold")).pack(pady=10)
        
        p1_full_list = sorted(new_p1, key=lambda x: int(x.split("OVR: ")[1]), reverse=True)
        p2_full_list = sorted(new_p2, key=lambda x: int(x.split("OVR: ")[1]), reverse=True)
        list_left.delete(0, tk.END); list_right.delete(0, tk.END)
        for k in p1_full_list: list_left.insert(tk.END, k)
        for k in p2_full_list: list_right.insert(tk.END, k)

        if current_round < max_rounds:
            current_round += 1
            tk.Button(container, text=f"⏭️ Next Round ({current_round})", bg="#FF9800", font=("Arial", 12, "bold"), command=lambda: [header.config(text=f"🔄 TRADE ROUND: {current_round} / {max_rounds}"), draw_p1_screen()]).pack(pady=20)
        else:
            tk.Button(container, text="🏆 SEE FINAL SQUADS", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), command=lambda: open_final_screen(tw)).pack(pady=20)

    draw_p1_screen()


def build_gui():
    global window, status_label, cb_trade_rounds, btn_trade
    global lbl_left, lbl_right, list_left, list_right, lbl_photo, lbl_photo_name
    global o1, o2, p1_t1, p1_t2, p1_t3, p1_t4, p2_t1, p2_t2, p2_t3, p2_t4
    global cb_p1_form, cb_p2_form

    window = tk.Tk()
    window.title("PES Draft - God Mode")
    window.geometry("1100x850"); window.configure(bg="#121212")
    tk.Label(window, text="🎲 PES DRAFT: GOD MODE", font=("Arial", 18, "bold"), bg="#121212", fg="#ffffff").pack(pady=5)

    top_panel = tk.Frame(window, bg="#121212"); top_panel.pack(pady=5)
    
    tk.Button(top_panel, text="📁 1. Load Players CSV", font=("Arial", 10, "bold"), bg="#2196F3", fg="white", command=select_csv).grid(row=0, column=0, padx=10)
    tk.Label(top_panel, text="Trade Rounds:", font=("Arial", 10, "bold"), bg="#121212", fg="white").grid(row=0, column=1, padx=(20,2))
    
    cb_trade_rounds = ttk.Combobox(top_panel, values=["1", "2", "3", "4", "5"], width=5, state="readonly")
    cb_trade_rounds.current(2); cb_trade_rounds.grid(row=0, column=2, padx=5)

    main_frame = tk.Frame(window, bg="#121212"); main_frame.pack(pady=5)
    
    form_names = list(FORMATIONS.keys())

    f_p1 = tk.LabelFrame(main_frame, text="Player 1 Arsenal", bg="#121212", fg="#2196F3", font=("Arial", 10, "bold"))
    f_p1.grid(row=0, column=0, padx=20, ipadx=10, ipady=10)
    o1 = tk.Entry(f_p1, width=15); o1.insert(0, "Player 1"); o1.grid(row=0, column=1)
    p1_t1 = ttk.Combobox(f_p1, width=25); p1_t1.grid(row=1, column=1, pady=2)
    p1_t2 = ttk.Combobox(f_p1, width=25); p1_t2.grid(row=2, column=1, pady=2)
    p1_t3 = ttk.Combobox(f_p1, width=25); p1_t3.grid(row=3, column=1, pady=2)
    p1_t4 = ttk.Combobox(f_p1, width=25); p1_t4.grid(row=4, column=1, pady=2)
    
    tk.Label(f_p1, text="Formation:", bg="#121212", fg="#2196F3").grid(row=5, column=0, pady=5)
    cb_p1_form = ttk.Combobox(f_p1, values=form_names, width=25, state="readonly")
    cb_p1_form.current(0); cb_p1_form.grid(row=5, column=1, pady=5)

    f_p2 = tk.LabelFrame(main_frame, text="Player 2 Arsenal", bg="#121212", fg="#f44336", font=("Arial", 10, "bold"))
    f_p2.grid(row=0, column=1, padx=20, ipadx=10, ipady=10)
    o2 = tk.Entry(f_p2, width=15); o2.insert(0, "Opponent"); o2.grid(row=0, column=1)
    p2_t1 = ttk.Combobox(f_p2, width=25); p2_t1.grid(row=1, column=1, pady=2)
    p2_t2 = ttk.Combobox(f_p2, width=25); p2_t2.grid(row=2, column=1, pady=2)
    p2_t3 = ttk.Combobox(f_p2, width=25); p2_t3.grid(row=3, column=1, pady=2)
    p2_t4 = ttk.Combobox(f_p2, width=25); p2_t4.grid(row=4, column=1, pady=2)
    
    tk.Label(f_p2, text="Formation:", bg="#121212", fg="#f44336").grid(row=5, column=0, pady=5)
    cb_p2_form = ttk.Combobox(f_p2, values=form_names, width=25, state="readonly")
    cb_p2_form.current(min(1, len(form_names)-1)); cb_p2_form.grid(row=5, column=1, pady=5)

    tk.Button(window, text="▶️ 2. START DRAFT", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=start_draft).pack(pady=5)

    status_label = tk.Label(window, text="System Ready. Load Players CSV first.", bg="#121212", fg="#aaaaaa"); status_label.pack()

    jumbo_frame = tk.Frame(window, bg="#000000", bd=2, relief=tk.RIDGE); jumbo_frame.pack(pady=5)
    lbl_photo = tk.Label(jumbo_frame, bg="#000000"); lbl_photo.pack()
    lbl_photo_name = tk.Label(jumbo_frame, text="Waiting for Next Star...", bg="#000000", fg="white", font=("Arial", 12, "bold")); lbl_photo_name.pack()

    list_frame = tk.Frame(window, bg="#121212"); list_frame.pack(pady=5, fill=tk.BOTH, expand=True, padx=20)
    frame_left = tk.Frame(list_frame, bg="#121212"); frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
    lbl_left = tk.Label(frame_left, text="Player 1", bg="#121212", fg="#2196F3", font=("Arial", 12, "bold")); lbl_left.pack()
    list_left = tk.Listbox(frame_left, bg="#000000", fg="#2196F3", font=("Consolas", 11)); list_left.pack(fill=tk.BOTH, expand=True)

    frame_right = tk.Frame(list_frame, bg="#121212"); frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
    lbl_right = tk.Label(frame_right, text="Player 2", bg="#121212", fg="#f44336", font=("Arial", 12, "bold")); lbl_right.pack()
    list_right = tk.Listbox(frame_right, bg="#000000", fg="#f44336", font=("Consolas", 11)); list_right.pack(fill=tk.BOTH, expand=True)

    btn_trade = tk.Button(window, text="🔄 OPEN TRADE ROOM", font=("Arial", 12, "bold"), bg="#FF9800", fg="black", command=open_trade_room, state=tk.DISABLED); btn_trade.pack(pady=10)

    window.mainloop()

# Arayüzü buradan tetikliyoruz
if __name__ == "__main__":
    build_gui()