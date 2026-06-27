import json
import os
import logging
import asyncio
from collections import defaultdict
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "")
BACKUP_CHANNEL_ID = os.environ.get("TELEGRAM_BACKUP_CHANNEL_ID", "")

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set!")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- COURSE LISTS ---

BACHELOR_COURSES = {
    "Economics with Data Science": [
        ("Teaching", "TEACHING"),
        ("Accounting and Big Data", "ECON-06/A"),
        ("Mathematics", "STAT-04/A"),
        ("Introduction to Economics", "ECON-01/A"),
        ("Statistics", "STAT-01/A"),
        ("Private Law", "GIUR-01/A"),
        ("Foreign Language", "L-LIN/02"),
        ("Business English", "L-LIN/12"),
        ("Management and Digital Technologies", "ECON-07/A"),
        ("Economic Statistics", "STAT-02/A"),
        ("Artificial Intelligence and Analytics", "STAT-01/A"),
        ("Business Law", "GIUR-03/A"),
        ("Farm Management and Rural Development", "AGRI-01/A"),
        ("Strategic Organization Design", "ECON-08/A"),
        ("Corporate Finance", "ECON-09/A"),
        ("Principles of Computer Science", "IINF-05/A"),
        ("Geographic Information System", "GEOG-01/B"),
        ("Public Economics", "ECON-03/A"),
        ("Data Analysis for Public Policy", "ECON-03/A"),
        ("International Economics", "ECON-01/A"),
        ("Labour Economics", "ECON-01/A"),
        ("Understanding Economic Data", "ECON-01/A"),
        ("Cyber International Law", "GIUR-09/A"),
        ("Data Management", "IINF-05/A"),
        ("Modern Data Analysis", "STAT-01/A")
    ],
    "Economics and Business": [
        ("Financial Accounting", "ECON-06/A"),
        ("Mathematics", "STAT-04/A"),
        ("Introduction to Economics", "ECON-01/A"),
        ("Statistics", "STAT-01/A"),
        ("Private Law", "GIUR-01/A"),
        ("Italian as Second Language", "L-LIN/02"),
        ("Business English", "L-LIN/12"),
        ("Introduction to Management", "ECON-07/A"),
        ("International Management", "ECON-07/A"),
        ("Economic History", "STEC-01/B"),
        ("Artificial Intelligence and Analytics", "STAT-01/A"),
        ("Business Law", "GIUR-03/A"),
        ("Environmental Policy", "GEOG-01/B"),
        ("Public Economics", "ECON-03/A"),
        ("Economics of Taxation", "ECON-03/A"),
        ("Economic Critical Thinking", "STEC-01/A"),
        ("Labour Economics", "ECON-01/A"),
        ("International Economics", "ECON-01/A"),
        ("European and Comparative Labour Law", "GIUR-04/A"),
        ("Farm Management and Rural Development", "AGRI-01/A"),
        ("Survey Methods in Social Research", "STAT-03/B"),
        ("Statistical Tools for Market Analysis", "STAT-02/A"),
        ("Strategic Organization Design", "ECON-08/A"),
        ("Corporate Finance", "ECON-09/A")
    ],
    "Industrial Engineering Technology": [
        ("Mathematics I", "MAT/05"),
        ("Fundamentals of Chemistry", "CHIM/07"),
        ("Principles of Computer Science", "ING-INF/05"),
        ("Italian as a Second Language", "L-LIN/02"),
        ("General Physics", "FIS/01"),
        ("Mathematics II", "MAT/05"),
        ("Probability and Information", "ING-INF/03"),
        ("Circuit Theory", "ING-IND/31"),
        ("Mechanics of Materials and Structures", "ICAR/08"),
        ("Mechanics of Machines", "ING-IND/13"),
        ("Economics for Engineers", "ING-IND/35"),
        ("Industrial and Environmental Measurements", "ING-IND/11"),
        ("Automatic Control", "ING-INF/04"),
        ("Thermodynamic and Heat Transfer", "ING-IND/10"),
        ("Industrial Plant Planning and Management", "ING-IND/17"),
        ("Materials Science and Engineering I", "ING-IND/22"),
        ("Fluid Machinery and Energy Systems", "ING-IND/08"),
        ("Fluid Mechanics", "ICAR/01"),
        ("Applied Mathematics", "MAT/05"),
        ("Geoengineering", "ICAR/07"),
        ("Digital Signal Processing", "ING-INF/03"),
        ("Introduction to Electromagnetism", "ING-INF/02"),
        ("Principles of Structural Design", "ICAR/09"),
        ("Computer Aided Design", "ING-IND/15"),
        ("Manufacturing Technologies", "ING-IND/16"),
        ("Hydraulics Design", "ICAR/02"),
        ("Advanced Programming Techniques", "ING-INF/05"),
        ("Fundamentals of Machine Design", "ING-IND/14"),
        ("Communication Networks", "ING-INF/03"),
        ("Air, Soil and Water Quality Management", "ICAR/03"),
        ("Antenna Foundations", "ING-INF/02"),
        ("Electronics", "ING-INF/01"),
        ("Metallurgy", "ING-IND/21"),
        ("Energy Management and Renewable Sources", "ING-IND/10")
    ]
}

MASTER_COURSES = {
    "Global Economy and Business (GLEB) (LM-56)": [
        ("Economics", "ECON-01/A"),
        ("Service Management", "ECON-07/A"),
        ("International Accounting", "ECON-06/A"),
        ("Applied Statistics and Data Analysis", "STAT-01/A"),
        ("Business Law", "GIUR-02/A"),
        ("Human Resources Management", "ECON-08/A"),
        ("Total Quality Management", "ECON-10/A"),
        ("Governance of Agri-Food Value Chains", "AGRI-01/A"),
        ("Mobility and Migration", "STAT-03/B"),
        ("Statistical Learning and Artificial Intelligence", "STAT-01/A"),
        ("Research Methods in Management", "STAT-01/A"),
        ("Economics and Policy for SMEs", "ECON-03/A"),
        ("Pension Economics", "ECON-01/A"),
        ("International Economics and Globalization", "ECON-01/A"),
        ("Development Economics", "ECON-02/A"),
        ("Advanced Public Economics", "ECON-03/A"),
        ("Applied Econometrics", "ECON-01/A")
    ],
    "Economics and Entrepreneurship (LM-56)": [
        ("Economics for Business", "ECON-01/A"),
        ("Accounting and Banking for SMEs", "ECON-09/B"),
        ("Entrepreneurship and Innovation", "ECON-01/A"),
        ("Business Law", "GIUR-02/A"),
        ("Soft Skills", "SOFT"),
        ("Entrepreneurship and Rural Development", "AGRI-01/A"),
        ("Historical Perspectives in Entrepreneurship and Technology", "STEC-01/A"),
        ("Digital Innovation in Organizations", "ECON-08/A"),
        ("Human Resources Management", "ECON-08/A"),
        ("Place Marketing", "ECON-07/A"),
        ("Applied Data Science for Economics", "STAT-01/A"),
        ("Marketing and Business Cases", "ECON-07/A"),
        ("Economics and Policy for SMEs", "ECON-03/A"),
        ("Development Economics", "ECON-02/A"),
        ("International Economics and Globalization (Part 1)", "ECON-01/A"),
        ("Applied Economics", "ECON-03/A")
    ],
    "Mechanical Engineering (LM-33)": [
        ("Mechanical Engineering Design", "ING-IND/14"),
        ("Measurement for Industrial Automation", "ING-IND/12"),
        ("Advanced Numerical Heat and Mass Transfer", "ING-IND/10"),
        ("Advanced Power Systems", "ING-IND/09"),
        ("Kinematics and Dynamics of Mechanisms", "ING-IND/13"),
        ("Advanced Manufacturing Processes", "ING-IND/16"),
        ("System and Human Reliability", "ING-IND/17"),
        ("Electric Power System Engineering", "ING-IND/33"),
        ("Electromagnetic Compatibility", "ING-IND/31"),
        ("Hybrid and Electric Vehicles", "ING-IND/32"),
        ("Introduction to Robotic Systems", "ING-INF/04"),
        ("Applied Metallurgy", "ING-IND/21"),
        ("Material Science and Engineering II", "ING-IND/22"),
        ("Design of Electronic Systems", "ING-INF/01")
    ],
    "Civil and Environmental Engineering (LM-23)": [
        ("Advanced Hydraulics", "ICAR/02"),
        ("Engineering Geology and Natural Risks", "GEO/05"),
        ("Geotechnical Design", "ICAR/07"),
        ("Earthquake Engineering", "ICAR/09"),
        ("Environmental Comfort and Air Quality", "ING-IND/10"),
        ("BIM Design Process", "ICAR/17"),
        ("Water Management", "ICAR/02"),
        ("Highway Design and Traffic Engineering", "ICAR/04"),
        ("Air, Soil and Water Quality Management", "ICAR/03"),
        ("Materials Science and Engineering", "ING-IND/22"),
        ("Measurement for Civil and Environmental Applications", "ING-INF/07"),
        ("System and Human Reliability", "ING-IND/17"),
        ("Electric Power System Engineering", "ING-IND/33"),
        ("Applied Metallurgy", "ING-IND/21"),
        ("Electromagnetic Compatibility", "ING-IND/31"),
        ("Italian as a Second Language", "L-LIN/02"),
        ("Soft Skills", "SOFT")
    ],
    "Telecommunications Engineering (LM-27)": [
        ("Methods of Applied Mathematics", "MAT/05"),
        ("Information Theory", "ING-INF/03"),
        ("Electromagnetic Field Theory", "ING-INF/02"),
        ("Instrumentation and Measurements for Communication Systems", "ING-INF/07"),
        ("Antennas and Radiowave Propagation", "ING-INF/02"),
        ("Digital Signal Processing", "ING-INF/03"),
        ("Advanced Communication Networks", "ING-INF/03"),
        ("Computer and Network Security", "ING-INF/05"),
        ("Electronics for Communication Systems", "ING-INF/01"),
        ("Microwave Theory and Devices", "ING-INF/02"),
        ("Telecommunications Systems", "ING-INF/03"),
        ("Digital Communications", "ING-INF/03"),
        ("Antenna Array Design", "ING-INF/02"),
        ("Radiowave Propagation in Urban Environments", "ING-INF/02"),
        ("Cryptography and Cybersecurity", "ING-INF/03"),
        ("Radar Systems", "ING-INF/03"),
        ("Electromagnetic Compatibility: Modeling and Measurements", "ING-IND/31"),
        ("Distributed Computing", "ING-INF/05"),
        ("Measurements for Cybersecurity Applications", "ING-INF/07")
    ]
}

# --- DATA STORAGE ---
DATA_FILE = "vault_data.json"
PROFILES_FILE = "user_profiles.json"


def migrate_old_entry(file_id):
    return {
        "files": [{"file_id": file_id, "file_type": "unknown"}],
        "uploader": "Anonymous",
        "uploader_id": 0,
        "uploaded_at": "before 2026",
        "ratings": {"up": 0, "down": 0}
    }


def load_vault():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        raw = json.load(f)
    vault = {}
    for key, entries in raw.items():
        migrated = []
        for entry in entries:
            if isinstance(entry, str):
                migrated.append(migrate_old_entry(entry))
            else:
                migrated.append(entry)
        vault[key] = migrated
    return vault


def load_profiles():
    if not os.path.exists(PROFILES_FILE):
        return {}
    with open(PROFILES_FILE, "r") as f:
        return json.load(f)


exam_vault = load_vault()
user_profiles = load_profiles()

user_sessions = {}
pending_photo_batches = defaultdict(lambda: {
    "user_id": None,
    "file_ids": [],
    "task": None,
    "lock": asyncio.Lock()
})


def save_vault():
    with open(DATA_FILE, "w") as f:
        json.dump(exam_vault, f, indent=2)


def save_profiles():
    with open(PROFILES_FILE, "w") as f:
        json.dump(user_profiles, f, indent=2)


# --- HELPERS ---

def get_nickname(user_id):
    return user_profiles.get(str(user_id), {}).get("nickname", "Anonymous")


def is_registered(user_id):
    return str(user_id) in user_profiles


def get_courses(level, major):
    if level == "Bachelor":
        return BACHELOR_COURSES.get(major, [])
    return MASTER_COURSES.get(major, [])


def get_majors(level):
    if level == "Bachelor":
        return list(BACHELOR_COURSES.keys())
    return list(MASTER_COURSES.keys())


def get_storage_key(level, ssd, exam_type, year):
    return f"{level}_{ssd}_{exam_type}_{year}"


def get_exam_types():
    return ["Final Exam", "Midterm", "Project", "Study Notes", "Oral Exam"]


def get_years():
    return ["2021", "2022", "2023", "2024", "2025", "2026", "Year Unknown"]


def get_course_display(course_tuple):
    return f"{course_tuple[0]} ({course_tuple[1]})"


def total_file_count(batches):
    return sum(len(b["files"]) for b in batches)


def get_user_profile_link(user_id: int) -> str:
    return f"tg://user?id={user_id}"


# --- REGISTRATION ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.message.from_user.id

    if not is_registered(user_id):
        user_sessions[user_id] = {"waiting_for_nickname": True}
        text = (
            "🏛️ **Welcome to UNICAS Exam Vault!** 🎓\n"
            "*University of Cassino and Southern Lazio*\n\n"
            "Before we start, what should we call you?\n\n"
            "✏️ **Type your name or nickname below:**\n"
            "_This is shown when you upload papers so students know who shared them._"
        )
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")
        return

    await show_main_menu(update, context, user_id)


async def show_main_menu(update, context, user_id):
    nickname = get_nickname(user_id)
    keyboard = [
        [InlineKeyboardButton("📤 Share (Contribute to the Vault)", callback_data="give")],
        [InlineKeyboardButton("📥 Receive (Access the Vault)", callback_data="receive")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")]
    ]
    text = (
        f"🏛️ **UNICAS Exam Vault** 🎓\n\n"
        f"Welcome back, **{nickname}**!\n\n"
        f"💪 Every paper you share helps a fellow student succeed.\n"
        f"📖 Every paper you download brings you closer to graduation.\n\n"
        f"**What would you like to do today?**"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )


# --- HELP & STATS ---

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **How to use this bot:**\n\n"
        "1️⃣ Click **Share** to upload your exam papers\n"
        "2️⃣ Select **Level** → **Major** → **Course** → **Exam Type** → **Year**\n"
        "3️⃣ Upload **PDFs or Photos**\n\n"
        "📥 Click **Receive** to download papers\n"
        "Browse by course and pick uploads by specific students!\n\n"
        "🔹 **Commands:**\n"
        "  /leaderboard - Top contributors\n"
        "  /stats - What's available\n"
        "  /setname <name> - Change your nickname\n"
        "  /myprofile - View your profile\n"
        "  /delete_me - Reset your profile\n"
        "  /tip - Support the bot ❤️",
        parse_mode="Markdown"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_keys = len(exam_vault)
    total_files = sum(total_file_count(b) for b in exam_vault.values())
    total_users = len(user_profiles)

    subject_list = []
    for key, batches in exam_vault.items():
        count = total_file_count(batches)
        if count > 0:
            parts = key.split("_")
            if len(parts) >= 4:
                subject_list.append(f"• {parts[0]} - {parts[1]} ({parts[2]}, {parts[3]}): {count} files")

    msg = (
        f"📊 **Exam Vault Statistics**\n\n"
        f"👥 Registered students: {total_users}\n"
        f"📁 Subjects with papers: {total_keys}\n"
        f"📄 Total files: {total_files}\n\n"
    )
    if subject_list:
        msg += "**Available Subjects:**\n" + "\n".join(subject_list[:20])
        if len(subject_list) > 20:
            msg += f"\n... and {len(subject_list) - 20} more!"
    else:
        msg += "❌ No papers uploaded yet!\nBe the first to donate!"

    await update.message.reply_text(msg, parse_mode="Markdown")


# --- LEADERBOARD ---

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_leaderboard(update, context)


async def send_leaderboard(update, context):
    upload_counts = {}
    for batches in exam_vault.values():
        for batch in batches:
            name = batch.get("uploader", "Anonymous")
            upload_counts[name] = upload_counts.get(name, 0) + len(batch["files"])

    sorted_leaders = sorted(upload_counts.items(), key=lambda x: x[1], reverse=True)

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, (name, count) in enumerate(sorted_leaders[:10]):
        medal = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{medal} **{name}** — {count} files")

    text = "🏆 **Top Contributors**\n\n"
    text += "\n".join(lines) if lines else "No uploads yet!"

    if update.callback_query:
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="home")]]
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(text, parse_mode="Markdown")


# --- TIP COMMAND ---

async def tip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❤️ **Show Some Love to the Bot Developers!**\n\n"
        "If UNICAS Exam Vault has helped you, consider showing your appreciation!\n\n"
        "👉 [Buy Me a Coffee](buymeacoffee.com/yourusername)\n\n"
        "Every tip helps keep the bot running 24/7 and expand to other universities.\n\n"
        "Thank you for being part of this community! 💪",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


# --- NICKNAME MANAGEMENT ---

async def setname_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if not context.args:
        current = user_profiles.get(user_id, {}).get("nickname", "Not set")
        await update.message.reply_text(
            f"📝 **Current nickname:** {current}\n\n"
            "✏️ To change it, use:\n"
            "`/setname Your New Name`\n\n"
            "Example: `/setname Marco Rossi`",
            parse_mode="Markdown"
        )
        return

    nickname = " ".join(context.args)
    if len(nickname) < 2:
        await update.message.reply_text("⚠️ Nickname must be at least 2 characters.")
        return
    if len(nickname) > 30:
        await update.message.reply_text("⚠️ Nickname too long! Max 30 characters.")
        return

    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "nickname": nickname,
            "registered_at": datetime.now().strftime("%Y-%m-%d"),
            "upload_count": 0
        }
    else:
        user_profiles[user_id]["nickname"] = nickname

    save_profiles()

    await update.message.reply_text(
        f"✅ **Nickname updated!**\n\n"
        f"Your new name is: **{nickname}**\n"
        f"Future uploads will use this name.",
        parse_mode="Markdown"
    )


async def myprofile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id not in user_profiles:
        await update.message.reply_text(
            "👤 **You don't have a profile yet!**\n\n"
            "Use /start to create one.",
            parse_mode="Markdown"
        )
        return

    profile = user_profiles[user_id]
    nickname = profile.get("nickname", "Not set")
    registered = profile.get("registered_at", "Unknown")
    upload_count = profile.get("upload_count", 0)

    total_files = 0
    for batches in exam_vault.values():
        for batch in batches:
            if batch.get("uploader_id") == int(user_id):
                total_files += len(batch["files"])

    upload_counts = {}
    for batches in exam_vault.values():
        for batch in batches:
            name = batch.get("uploader", "Anonymous")
            upload_counts[name] = upload_counts.get(name, 0) + len(batch["files"])

    sorted_leaders = sorted(upload_counts.items(), key=lambda x: x[1], reverse=True)
    rank = 1
    for i, (name, count) in enumerate(sorted_leaders):
        if name == nickname:
            rank = i + 1
            break

    await update.message.reply_text(
        f"👤 **Your Profile**\n\n"
        f"📝 Nickname: **{nickname}**\n"
        f"📅 Registered: {registered}\n"
        f"📤 Uploads: {upload_count} batch(es)\n"
        f"📄 Total files uploaded: {total_files}\n"
        f"🏆 Rank: #{rank} on leaderboard\n\n"
        f"✏️ To change your name: `/setname NewName`\n"
        f"🗑️ To delete your profile: `/delete_me`",
        parse_mode="Markdown"
    )


async def delete_me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id not in user_profiles:
        await update.message.reply_text(
            "👤 **You don't have a profile to delete.**\n\n"
            "Use /start to create one.",
            parse_mode="Markdown"
        )
        return

    nickname = user_profiles[user_id].get("nickname", "Unknown")

    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, delete my profile", callback_data="confirm_delete_yes"),
            InlineKeyboardButton("❌ No, cancel", callback_data="confirm_delete_no")
        ]
    ]
    await update.message.reply_text(
        f"⚠️ **Are you sure you want to delete your profile?**\n\n"
        f"👤 Nickname: **{nickname}**\n\n"
        f"⚠️ This will NOT delete your uploaded files.\n"
        f"⚠️ You can create a new profile with /start anytime.\n\n"
        f"**What would you like to do?**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def confirm_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = query.data

    if data == "confirm_delete_yes":
        if user_id in user_profiles:
            del user_profiles[user_id]
            save_profiles()
            await query.edit_message_text(
                "🗑️ **Your profile has been deleted.**\n\n"
                "Next time you use /start, you'll be asked to set a new nickname.\n\n"
                "📂 Your uploaded files are still in the vault.",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "⚠️ Your profile was already deleted.",
                parse_mode="Markdown"
            )
    else:
        await query.edit_message_text(
            "✅ **Profile deletion cancelled.**\n\n"
            "Your profile is safe!",
            parse_mode="Markdown"
        )


# --- REPLACE COMMAND ---

async def replace_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return

    if not context.args:
        await update.message.reply_text(
            "🔄 **How to replace files:**\n\n"
            "1. Find the storage key of the file you want to replace\n"
            "2. Send the command: `/replace <storage_key>`\n"
            "3. Upload the improved file\n\n"
            "Example: `/replace Bachelor_STAT-01/A_Final Exam_2024`\n\n"
            "📌 You can find storage keys in the backup channel or using /list",
            parse_mode="Markdown"
        )
        return

    storage_key = " ".join(context.args)
    user_sessions[int(user_id)]["replace_key"] = storage_key
    user_sessions[int(user_id)]["action"] = "replace"

    await update.message.reply_text(
        f"📂 **Storage Key:** `{storage_key}`\n\n"
        f"📎 Now send the improved file (PDF or photo).\n\n"
        f"⚠️ This will replace ALL files in this batch!\n"
        f"Use /cancel to cancel.",
        parse_mode="Markdown"
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_sessions[user_id] = {}
    await update.message.reply_text("✅ Operation cancelled.")


# --- ENHANCED ADMIN ---

async def admin_enhanced_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return

    total_users = len(user_profiles)
    total_subjects = len(exam_vault)
    total_files = sum(total_file_count(b) for b in exam_vault.values())

    upload_counts = {}
    for batches in exam_vault.values():
        for batch in batches:
            name = batch.get("uploader", "Anonymous")
            upload_counts[name] = upload_counts.get(name, 0) + len(batch["files"])

    top = sorted(upload_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_text = "\n".join([f"  • {n}: {c} files" for n, c in top]) or "  No uploads yet"

    keyboard = [
        [InlineKeyboardButton("🗂 Manage Files", callback_data="adm_manage")],
        [InlineKeyboardButton("👥 View All Users", callback_data="adm_all_users")],
        [InlineKeyboardButton("📊 Full Stats", callback_data="adm_stats")],
        [InlineKeyboardButton("🏠 Home", callback_data="home")]
    ]

    text = (
        f"🛠 **Enhanced Admin Panel**\n\n"
        f"👥 Registered users: {total_users}\n"
        f"📁 Subjects: {total_subjects}\n"
        f"📄 Total files: {total_files}\n\n"
        f"🏆 **Top Uploaders:**\n{top_text}"
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return

    if not user_profiles:
        await update.message.reply_text("📭 No users registered yet.")
        return

    message = "👥 **All Users**\n\n"

    for uid, profile in user_profiles.items():
        nickname = profile.get("nickname", "Unknown")
        uploads = profile.get("upload_count", 0)
        profile_link = get_user_profile_link(int(uid))
        message += f"👤 **{nickname}**\n"
        message += f"   📤 Uploads: {uploads}\n"
        message += f"   🔗 [Open Profile]({profile_link})\n\n"

    await update.message.reply_text(message, parse_mode="Markdown")


async def userinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return

    if not context.args:
        await update.message.reply_text(
            "🔍 **User Info:**\n\n"
            "Usage: `/userinfo <user_id>`\n\n"
            "Get details about a specific user.\n"
            "Example: `/userinfo 123456789`",
            parse_mode="Markdown"
        )
        return

    target_id = context.args[0]

    if target_id not in user_profiles:
        await update.message.reply_text(f"❌ User not found: `{target_id}`", parse_mode="Markdown")
        return

    profile = user_profiles[target_id]
    nickname = profile.get("nickname", "Unknown")
    registered = profile.get("registered_at", "Unknown")
    upload_count = profile.get("upload_count", 0)

    total_files = 0
    for batches in exam_vault.values():
        for batch in batches:
            if batch.get("uploader_id") == int(target_id):
                total_files += len(batch["files"])

    uploads = []
    for key, batches in exam_vault.items():
        for batch in batches:
            if batch.get("uploader_id") == int(target_id):
                uploads.append(f"  • {key} ({len(batch['files'])} files)")

    uploads_text = "\n".join(uploads[:5]) if uploads else "  No uploads found"
    if len(uploads) > 5:
        uploads_text += f"\n  ... and {len(uploads) - 5} more"

    profile_link = get_user_profile_link(int(target_id))

    text = (
        f"👤 **User Profile**\n\n"
        f"📝 Nickname: **{nickname}**\n"
        f"🆔 User ID: `{target_id}`\n"
        f"🔗 [Open Profile]({profile_link})\n"
        f"📅 Registered: {registered}\n"
        f"📤 Upload batches: {upload_count}\n"
        f"📄 Total files: {total_files}\n\n"
        f"📂 **Uploads:**\n{uploads_text}"
    )

    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)


async def delete_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return

    if not context.args:
        await update.message.reply_text(
            "🗑️ **Delete User:**\n\n"
            "Usage: `/delete_user <user_id>`\n\n"
            "⚠️ This only deletes the user's profile,\n"
            "NOT their uploaded files.",
            parse_mode="Markdown"
        )
        return

    target_id = context.args[0]

    if target_id not in user_profiles:
        await update.message.reply_text(f"❌ User not found: `{target_id}`", parse_mode="Markdown")
        return

    nickname = user_profiles[target_id].get("nickname", "Unknown")

    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, delete profile", callback_data=f"del_user_confirm_{target_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="del_user_cancel")
        ]
    ]

    await update.message.reply_text(
        f"⚠️ **Delete User Profile?**\n\n"
        f"👤 User: **{nickname}**\n"
        f"🆔 ID: `{target_id}`\n\n"
        f"⚠️ This will delete their profile data.\n"
        f"📂 Uploaded files will remain in the vault.\n\n"
        f"Are you sure?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return
    await update.message.reply_text("⏳ Starting backup to channel...")
    await do_full_backup(context, update.message.chat_id)


async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return
    if not exam_vault:
        await update.message.reply_text("📭 No files stored!")
        return
    lines = [f"• {k}: {total_file_count(v)} files" for k, v in exam_vault.items()]
    await update.message.reply_text("📂 **All Subjects:**\n\n" + "\n".join(lines), parse_mode="Markdown")


# --- CHANNEL BACKUP ---

async def testchannel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return

    if not BACKUP_CHANNEL_ID:
        await update.message.reply_text("⚠️ BACKUP_CHANNEL_ID is not set in Secrets!")
        return

    try:
        await context.bot.send_message(
            chat_id=BACKUP_CHANNEL_ID,
            text="✅ **Test message from bot!**\n\nIf you see this, the backup channel is working!",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ Test message sent to channel!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}\n\nCheck that:\n1. Channel ID is correct\n2. Bot is admin in the channel\n3. Bot has 'Post Messages' permission")


async def backfill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return

    if not BACKUP_CHANNEL_ID:
        await update.message.reply_text("⚠️ BACKUP_CHANNEL_ID is not set in Secrets!")
        return

    await update.message.reply_text("⏳ Starting backfill... This may take a while.")

    total_files = 0
    total_batches = 0
    errors = 0

    try:
        for storage_key, batches in exam_vault.items():
            for batch in batches:
                try:
                    uploader = batch.get("uploader", "Anonymous")
                    date = batch.get("uploaded_at", "unknown")
                    caption = (
                        f"🗂 **BACKUP (BACKFILL)**\n"
                        f"🔑 `{storage_key}`\n"
                        f"👤 {uploader} · {date}"
                    )

                    sent_count = 0
                    for i, file_info in enumerate(batch["files"]):
                        file_id = file_info["file_id"]
                        file_type = file_info.get("file_type", "unknown")
                        cap = caption if i == 0 else None

                        try:
                            if file_type == "photo":
                                await context.bot.send_photo(
                                    chat_id=BACKUP_CHANNEL_ID,
                                    photo=file_id,
                                    caption=cap,
                                    parse_mode="Markdown"
                                )
                            else:
                                await context.bot.send_document(
                                    chat_id=BACKUP_CHANNEL_ID,
                                    document=file_id,
                                    caption=cap,
                                    parse_mode="Markdown"
                                )
                            sent_count += 1
                        except Exception as e:
                            logging.error(f"Failed to send file: {e}")
                            errors += 1

                    total_files += sent_count
                    total_batches += 1

                except Exception as e:
                    logging.error(f"Failed to process batch: {e}")
                    errors += 1

        await update.message.reply_text(
            f"✅ **Backfill Complete!**\n\n"
            f"📁 Subjects processed: {len(exam_vault)}\n"
            f"📤 Batches sent: {total_batches}\n"
            f"📄 Files sent: {total_files}\n"
            f"⚠️ Errors: {errors}\n\n"
            f"Check your backup channel to see all files!"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Backfill failed: {e}")


async def do_full_backup(context, chat_id):
    if not BACKUP_CHANNEL_ID:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ No backup channel configured.")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_files = sum(total_file_count(b) for b in exam_vault.values())
    summary = (
        f"📦 **Vault Backup** — {now}\n"
        f"📁 Subjects: {len(exam_vault)}\n"
        f"📄 Total files: {total_files}\n"
        f"👥 Users: {len(user_profiles)}"
    )

    try:
        await context.bot.send_message(chat_id=BACKUP_CHANNEL_ID, text=summary, parse_mode="Markdown")

        with open(DATA_FILE, "rb") as f:
            await context.bot.send_document(
                chat_id=BACKUP_CHANNEL_ID,
                document=f,
                filename=f"vault_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                caption="vault_data.json"
            )

        if os.path.exists(PROFILES_FILE):
            with open(PROFILES_FILE, "rb") as f:
                await context.bot.send_document(
                    chat_id=BACKUP_CHANNEL_ID,
                    document=f,
                    filename=f"user_profiles_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    caption="user_profiles.json"
                )

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ **Backup complete!**\n\n{summary}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Full backup failed: {e}")
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Backup failed: {e}")


# --- BUTTON HANDLERS ---

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "leaderboard":
        await send_leaderboard(update, context)
        return

    if data == "home":
        await show_main_menu(update, context, user_id)
        return

    # --- GIVE FLOW ---
    if data == "give":
        keyboard = [
            [InlineKeyboardButton("🎓 Bachelor", callback_data="give_level_Bachelor")],
            [InlineKeyboardButton("🎓 Master", callback_data="give_level_Master")],
            [InlineKeyboardButton("⬅️ Back", callback_data="home")]
        ]
        await query.edit_message_text(
            "📚 **Select your academic level:**",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif data.startswith("give_level_"):
        level = data.split("_")[2]
        user_sessions[user_id] = {"action": "give", "level": level}
        majors = get_majors(level)
        keyboard = [[InlineKeyboardButton(f"📘 {m}", callback_data=f"give_major_{m}")] for m in majors]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="give")])
        await query.edit_message_text(
            f"✅ **{level} student!**\n\nSelect your **Major:**",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif data.startswith("give_major_"):
        major = data.replace("give_major_", "")
        user_sessions[user_id]["major"] = major
        level = user_sessions[user_id]["level"]
        courses = get_courses(level, major)
        keyboard = [
            [InlineKeyboardButton(f"📖 {get_course_display(c)}", callback_data=f"give_course_{c[1]}")]
            for c in courses
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"give_level_{level}")])
        await query.edit_message_text(
            f"📖 **Select your Course:**\n📍 {level} - {major}",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif data.startswith("give_course_"):
        ssd = data.replace("give_course_", "")
        user_sessions[user_id]["ssd"] = ssd
        keyboard = [
            [InlineKeyboardButton(f"📝 {t}", callback_data=f"give_type_{t}")]
            for t in get_exam_types()
        ]
        level = user_sessions[user_id]["level"]
        major = user_sessions[user_id].get("major", "")
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"give_major_{major}")])
        await query.edit_message_text(
            "📂 **Select the exam type:**",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif data.startswith("give_type_"):
        exam_type = data.replace("give_type_", "")
        user_sessions[user_id]["exam_type"] = exam_type
        years = get_years()
        keyboard = []
        row = []
        for y in years:
            row.append(InlineKeyboardButton(y, callback_data=f"give_year_{y}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("✏️ Enter year manually", callback_data="give_year_other")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"give_course_{user_sessions[user_id].get('ssd', '')}")])
        await query.edit_message_text(
            f"📝 **{exam_type}**\n\nSelect the **year:**",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif data.startswith("give_year_"):
        year = data.replace("give_year_", "")
        if year == "other":
            user_sessions[user_id]["waiting_for_year"] = True
            await query.edit_message_text(
                "✏️ **Type the year** in the chat below.\nExample: *2024*",
                parse_mode="Markdown"
            )
        else:
            user_sessions[user_id]["year"] = year
            await ask_for_upload(query, user_id)

    # --- RECEIVE FLOW ---
    elif data == "receive":
        keyboard = [
            [InlineKeyboardButton("🎓 Bachelor", callback_data="rec_level_Bachelor")],
            [InlineKeyboardButton("🎓 Master", callback_data="rec_level_Master")],
            [InlineKeyboardButton("⬅️ Back", callback_data="home")]
        ]
        await query.edit_message_text(
            "📚 **Select your academic level:**",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif data.startswith("rec_level_"):
        level = data.split("_")[2]
        user_sessions[user_id] = {"action": "receive", "level": level}
        majors = get_majors(level)
        keyboard = [[InlineKeyboardButton(f"📘 {m}", callback_data=f"rec_major_{m}")] for m in majors]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="receive")])
        await query.edit_message_text(
            f"✅ **{level} student!**\n\nSelect your **Major:**",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif data.startswith("rec_major_"):
        major = data.replace("rec_major_", "")
        user_sessions[user_id]["major"] = major
        level = user_sessions[user_id]["level"]
        courses = get_courses(level, major)
        keyboard = [
            [InlineKeyboardButton(f"📖 {get_course_display(c)}", callback_data=f"rec_course_{c[1]}")]
            for c in courses
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"rec_level_{level}")])
        await query.edit_message_text(
            f"📖 **Select your Course:**\n📍 {level} - {major}",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif data.startswith("rec_course_"):
        ssd = data.replace("rec_course_", "")
        user_sessions[user_id]["ssd"] = ssd
        level = user_sessions[user_id]["level"]

        categories = {}
        for key, batches in exam_vault.items():
            parts = key.split("_")
            if len(parts) >= 4 and parts[0] == level and parts[1] == ssd:
                exam_type = parts[2]
                year = parts[3]
                display = f"{exam_type} {year}"
                count = total_file_count(batches)
                if count > 0:
                    categories[display] = {"key": key, "count": count, "batches": len(batches)}

        if categories:
            keyboard = []
            for display, info in categories.items():
                label = f"📂 {display} — {info['count']} file(s) from {info['batches']} student(s)"
                keyboard.append([InlineKeyboardButton(label, callback_data=f"rec_cat_{display}")])
            major = user_sessions[user_id].get("major", "")
            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"rec_major_{major}")])
            user_sessions[user_id]["categories"] = categories
            await query.edit_message_text(
                "📂 **Available papers — select a category:**",
                reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )
        else:
            major = user_sessions[user_id].get("major", "")
            keyboard = [
                [InlineKeyboardButton("📤 I have papers for this course!", callback_data=f"rec_upload_{ssd}")],
                [InlineKeyboardButton("⬅️ Back", callback_data=f"rec_major_{major}")],
                [InlineKeyboardButton("🏠 Home", callback_data="home")]
            ]
            await query.edit_message_text(
                "😅 **No papers found for this course yet.**\n\nBe the first to contribute!",
                reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )

    elif data.startswith("rec_cat_"):
        display = data.replace("rec_cat_", "")
        categories = user_sessions[user_id].get("categories", {})
        if display not in categories:
            await query.edit_message_text("⚠️ Session expired. Use /start to begin again.")
            return

        storage_key = categories[display]["key"]
        user_sessions[user_id]["current_key"] = storage_key
        user_sessions[user_id]["current_display"] = display
        batches = exam_vault.get(storage_key, [])

        keyboard = []
        for i, batch in enumerate(batches):
            uploader = batch.get("uploader", "Anonymous")
            count = len(batch["files"])
            file_type = batch["files"][0].get("file_type", "file") if batch["files"] else "file"
            type_icon = "🖼️" if file_type == "photo" else "📄"
            file_word = "photo" if file_type == "photo" else "file"
            ratings = batch.get("ratings", {"up": 0, "down": 0})
            up, down = ratings.get("up", 0), ratings.get("down", 0)
            rating_str = f" · 👍{up} 👎{down}" if (up + down) > 0 else ""
            label = f"{type_icon} {count} {file_word}{'s' if count > 1 else ''} from {uploader}{rating_str}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"rec_batch_{i}")])

        keyboard.append([InlineKeyboardButton("📦 Download All", callback_data="rec_all")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"rec_course_{user_sessions[user_id]['ssd']}")])

        await query.edit_message_text(
            f"📂 **{display}**\n\nSelect whose upload to download:",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif data.startswith("rec_batch_"):
        index = int(data.replace("rec_batch_", ""))
        storage_key = user_sessions[user_id].get("current_key")
        batches = exam_vault.get(storage_key, [])
        if index >= len(batches):
            await query.edit_message_text("⚠️ Not found. Use /start to begin again.")
            return

        batch = batches[index]
        await query.edit_message_text(
            f"⏳ Sending files from **{batch.get('uploader', 'Anonymous')}**...",
            parse_mode="Markdown"
        )
        sent = await send_batch_files(context, query.message.chat_id, [batch])
        user_sessions[user_id]["last_rated_key"] = storage_key
        user_sessions[user_id]["last_rated_index"] = index
        await send_rating_prompt(context, query.message.chat_id, index)
        display = user_sessions[user_id].get("current_display", "")
        nav_keyboard = [
            [InlineKeyboardButton("⬅️ Back to uploads", callback_data=f"rec_cat_{display}")],
            [InlineKeyboardButton("🏠 Give / Receive", callback_data="home")]
        ]
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"✅ **Sent {sent} file(s)**\n\n📚 Good luck with your studies! 🍀",
            reply_markup=InlineKeyboardMarkup(nav_keyboard),
            parse_mode="Markdown"
        )

    elif data == "rec_all":
        storage_key = user_sessions[user_id].get("current_key")
        batches = exam_vault.get(storage_key, [])
        await query.edit_message_text("⏳ Sending all files...", parse_mode="Markdown")
        sent = await send_batch_files(context, query.message.chat_id, batches)
        display = user_sessions[user_id].get("current_display", "")
        nav_keyboard = [
            [InlineKeyboardButton("⬅️ Back to uploads", callback_data=f"rec_cat_{display}")],
            [InlineKeyboardButton("🏠 Give / Receive", callback_data="home")]
        ]
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"✅ **Sent {sent} file(s)**\n\n📚 Good luck with your studies! 🍀",
            reply_markup=InlineKeyboardMarkup(nav_keyboard),
            parse_mode="Markdown"
        )

    elif data.startswith("rec_upload_"):
        ssd = data.replace("rec_upload_", "")
        user_sessions[user_id]["ssd"] = ssd
        user_sessions[user_id]["action"] = "give"
        keyboard = [
            [InlineKeyboardButton(f"📝 {t}", callback_data=f"give_type_{t}")]
            for t in get_exam_types()
        ]
        await query.edit_message_text(
            "📂 **Upload your papers!**\n\nSelect the **exam type:**",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    # --- RATING ---
    elif data.startswith("rate_"):
        parts = data.split("_")
        vote = parts[1]
        try:
            batch_index = int(parts[2])
        except (IndexError, ValueError):
            batch_index = -1

        storage_key = user_sessions[user_id].get("last_rated_key")
        if storage_key and batch_index >= 0:
            batches = exam_vault.get(storage_key, [])
            if batch_index < len(batches):
                if vote == "up":
                    batches[batch_index]["ratings"]["up"] += 1
                    save_vault()
                    await query.edit_message_text("👍 Thanks for the positive rating!")
                elif vote == "down":
                    batches[batch_index]["ratings"]["down"] += 1
                    save_vault()
                    await query.edit_message_text("👎 Thanks for the feedback!")
        else:
            await query.answer("Rating saved!", show_alert=False)

    # --- MORE UPLOAD OPTIONS ---
    elif data.startswith("more_"):
        choice = data.replace("more_", "")
        if choice == "ask":
            keyboard = [
                [InlineKeyboardButton("📤 Yes, same subject", callback_data="more_same")],
                [InlineKeyboardButton("📤 Yes, different subject", callback_data="more_different")],
                [InlineKeyboardButton("🙅 No, that's all for now", callback_data="more_done")]
            ]
            await query.edit_message_text(
                "📎 **Do you have other documents to upload?**",
                reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )
        elif choice == "same":
            keyboard = [
                [InlineKeyboardButton(f"📝 {t}", callback_data=f"give_type_{t}")]
                for t in get_exam_types()
            ]
            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="more_ask")])
            await query.edit_message_text(
                "📂 **Same Course** — Select exam type:",
                reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )
        elif choice == "different":
            keyboard = [
                [InlineKeyboardButton("🎓 Bachelor", callback_data="give_level_Bachelor")],
                [InlineKeyboardButton("🎓 Master", callback_data="give_level_Master")],
                [InlineKeyboardButton("⬅️ Back", callback_data="more_ask")]
            ]
            await query.edit_message_text(
                "📚 **Select your academic level:**",
                reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )
        elif choice == "done":
            nickname = get_nickname(user_id)
            keyboard = [[InlineKeyboardButton("🏠 Give / Receive", callback_data="home")]]
            await query.edit_message_text(
                f"🎉 **Thank you, {nickname}!**\n\n"
                "You're now a UNICAS Exam Vault HERO! 🦸‍♂️\n"
                "Your contribution helps your fellow students succeed!\n\n"
                "📚 Every file you share brings someone closer to graduation. You're awesome! 💪",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

    # --- ADMIN CALLBACKS ---
    elif data == "adm_manage":
        if str(user_id) != ADMIN_CHAT_ID:
            await query.answer("Unauthorized", show_alert=True)
            return
        keys = list(exam_vault.keys())
        user_sessions[user_id]["adm_keys"] = keys
        keyboard = []
        for i, key in enumerate(keys[:20]):
            count = total_file_count(exam_vault[key])
            keyboard.append([InlineKeyboardButton(f"🗂 {key[:40]} ({count} files)", callback_data=f"adm_key_{i}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="adm_back")])
        await query.edit_message_text(
            "🗂 **Select a subject to manage:**",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif data.startswith("adm_key_"):
        if str(user_id) != ADMIN_CHAT_ID:
            await query.answer("Unauthorized", show_alert=True)
            return
        key_index = int(data.replace("adm_key_", ""))
        keys = user_sessions[user_id].get("adm_keys", [])
        if key_index >= len(keys):
            await query.edit_message_text("⚠️ Session expired.")
            return
        storage_key = keys[key_index]
        user_sessions[user_id]["adm_current_key"] = storage_key
        batches = exam_vault.get(storage_key, [])
        keyboard = []
        for i, batch in enumerate(batches):
            uploader = batch.get("uploader", "?")
            count = len(batch["files"])
            ratings = batch.get("ratings", {"up": 0, "down": 0})
            keyboard.append([InlineKeyboardButton(
                f"🗑 Delete Upload {i+1} by {uploader} ({count} files) 👍{ratings['up']} 👎{ratings['down']}",
                callback_data=f"adm_del_{i}"
            )])
        keyboard.append([InlineKeyboardButton("🗑 Delete Entire Subject", callback_data="adm_del_all")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="adm_manage")])
        await query.edit_message_text(
            f"🗂 **Managing:** `{storage_key}`\n\nSelect an upload to delete:",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif data.startswith("adm_del_"):
        if str(user_id) != ADMIN_CHAT_ID:
            await query.answer("Unauthorized", show_alert=True)
            return
        storage_key = user_sessions[user_id].get("adm_current_key")
        if not storage_key:
            await query.edit_message_text("⚠️ Session expired.")
            return
        suffix = data.replace("adm_del_", "")
        if suffix == "all":
            del exam_vault[storage_key]
            save_vault()
            await query.edit_message_text(f"✅ Deleted entire subject: `{storage_key}`", parse_mode="Markdown")
        else:
            batch_index = int(suffix)
            batches = exam_vault.get(storage_key, [])
            if batch_index < len(batches):
                removed = batches.pop(batch_index)
                if not batches:
                    del exam_vault[storage_key]
                save_vault()
                await query.edit_message_text(
                    f"✅ Deleted upload by **{removed.get('uploader', '?')}** from `{storage_key}`",
                    parse_mode="Markdown"
                )

    elif data == "adm_back":
        await admin_enhanced_command(update, context)

    elif data == "adm_all_users":
        if str(user_id) != ADMIN_CHAT_ID:
            await query.answer("Unauthorized", show_alert=True)
            return

        if not user_profiles:
            await query.edit_message_text("📭 No users registered yet.")
            return

        keyboard = []
        for uid, profile in user_profiles.items():
            nickname = profile.get("nickname", "Unknown")
            upload_count = profile.get("upload_count", 0)
            profile_link = get_user_profile_link(int(uid))
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 {nickname} ({upload_count} uploads) 🔗",
                    url=profile_link
                )
            ])

        keyboard.append([InlineKeyboardButton("⬅️ Back to Admin", callback_data="adm_back")])

        await query.edit_message_text(
            f"👥 **All Users ({len(user_profiles)})**\n\n"
            f"📌 Click any user below to view their Telegram profile:\n\n"
            f"_The 🔗 icon means the button opens their profile._",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "adm_stats":
        if str(user_id) != ADMIN_CHAT_ID:
            await query.answer("Unauthorized", show_alert=True)
            return

        total_users = len(user_profiles)
        total_subjects = len(exam_vault)
        total_files = sum(total_file_count(b) for b in exam_vault.values())

        subject_counts = {}
        for key, batches in exam_vault.items():
            parts = key.split("_")
            if len(parts) >= 4:
                subject = parts[1]
                subject_counts[subject] = subject_counts.get(subject, 0) + len(batches)

        sorted_subjects = sorted(subject_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        subject_text = "\n".join([f"  • {s}: {c} batches" for s, c in sorted_subjects]) or "  No subjects"

        text = (
            f"📊 **Full Statistics**\n\n"
            f"👥 Registered users: {total_users}\n"
            f"📁 Subjects with files: {total_subjects}\n"
            f"📄 Total files: {total_files}\n\n"
            f"📂 **Top Subjects by Batch:**\n{subject_text}\n\n"
            f"🔍 Use /stats for general info\n"
            f"🔍 Use /list to see all storage keys"
        )

        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="adm_back")]]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data.startswith("del_user_confirm_"):
        target_id = data.replace("del_user_confirm_", "")
        if target_id in user_profiles:
            nickname = user_profiles[target_id].get("nickname", "Unknown")
            del user_profiles[target_id]
            save_profiles()
            await query.edit_message_text(
                f"🗑️ **User deleted!**\n\n"
                f"👤 {nickname} (ID: `{target_id}`) has been removed.\n\n"
                f"📂 Their files are still in the vault.",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ User not found.")

    elif data == "del_user_cancel":
        await query.edit_message_text("✅ Deletion cancelled.")


# --- FILE HANDLERS ---

async def send_batch_files(context, chat_id, batches):
    sent = 0
    for batch in batches:
        for file_info in batch["files"]:
            file_id = file_info["file_id"]
            file_type = file_info.get("file_type", "unknown")
            try:
                if file_type == "photo":
                    await context.bot.send_photo(chat_id=chat_id, photo=file_id)
                else:
                    await context.bot.send_document(chat_id=chat_id, document=file_id)
                sent += 1
            except Exception:
                try:
                    await context.bot.send_photo(chat_id=chat_id, photo=file_id)
                    sent += 1
                except Exception:
                    try:
                        await context.bot.send_document(chat_id=chat_id, document=file_id)
                        sent += 1
                    except Exception:
                        pass
    return sent


async def send_rating_prompt(context, chat_id, batch_index):
    keyboard = [
        [
            InlineKeyboardButton(f"👍 Helpful", callback_data=f"rate_up_{batch_index}"),
            InlineKeyboardButton(f"👎 Not helpful", callback_data=f"rate_down_{batch_index}")
        ]
    ]
    await context.bot.send_message(
        chat_id=chat_id,
        text="⭐ **Rate these files** — was this upload helpful?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def ask_for_upload(query, user_id):
    session = user_sessions[user_id]
    await query.edit_message_text(
        f"✅ **Ready to Upload!**\n\n"
        f"📝 Exam Type: **{session.get('exam_type')}**\n"
        f"📅 Year: **{session.get('year')}**\n\n"
        f"📎 **Now upload your exam paper!**\n\n"
        f"📄 Send a **PDF** file\n"
        f"🖼️ Or send **Photos** (you can send multiple)\n\n"
        f"📤 Your name will be attached to your upload!",
        parse_mode="Markdown"
    )


async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    session = user_sessions.get(user_id, {})

    # --- REPLACE MODE ---
    if session.get("action") == "replace":
        storage_key = session.get("replace_key")
        if not storage_key:
            await update.message.reply_text("⚠️ Session expired. Use /replace again.")
            return

        if update.message.document or update.message.photo:
            if update.message.document:
                file_id = update.message.document.file_id
                file_type = "pdf"
            else:
                file_id = update.message.photo[-1].file_id
                file_type = "photo"

            if storage_key in exam_vault and exam_vault[storage_key]:
                batch = exam_vault[storage_key][0]
                old_files = batch["files"]
                batch["files"] = [{"file_id": file_id, "file_type": file_type}]
                save_vault()

                await update.message.reply_text(
                    f"✅ **File Replaced!**\n\n"
                    f"🔑 `{storage_key}`\n"
                    f"📄 Type: {file_type}\n"
                    f"👤 Uploader: {batch.get('uploader', 'Anonymous')}\n\n"
                    f"⚠️ Replaced {len(old_files)} file(s) with the new one.",
                    parse_mode="Markdown"
                )

                asyncio.create_task(backup_files_to_channel(context, storage_key, batch))
                user_sessions[user_id] = {}
            else:
                await update.message.reply_text(f"❌ Storage key not found: `{storage_key}`", parse_mode="Markdown")
            return
        else:
            await update.message.reply_text("⚠️ Please send a PDF or Photo file.")
            return

    # --- NORMAL UPLOAD FLOW ---
    if session.get("action") != "give":
        await update.message.reply_text(
            "⚠️ Please use /start first and select **Share** to upload files!",
            parse_mode="Markdown"
        )
        return

    level = session.get("level")
    ssd = session.get("ssd")
    exam_type = session.get("exam_type")
    year = session.get("year")

    if not all([level, ssd, exam_type, year]):
        await update.message.reply_text("⚠️ Please complete the course selection first via the menu!")
        return

    if update.message.document:
        await handle_pdf(update, context, user_id, level, ssd, exam_type, year)
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        unique_key = f"{user_id}_{level}_{ssd}_{exam_type}_{year}"

        async with pending_photo_batches[unique_key]["lock"]:
            batch = pending_photo_batches[unique_key]
            if not batch["file_ids"]:
                batch["user_id"] = user_id
                batch["file_ids"] = [file_id]
                batch["task"] = asyncio.create_task(
                    process_photo_batch(unique_key, user_id, level, ssd, exam_type, year, update, context)
                )
            else:
                batch["file_ids"].append(file_id)

        await update.message.reply_text("⏳ Photo received, waiting for more...")
    else:
        await update.message.reply_text("⚠️ Please send a **PDF** or **Photo** file!", parse_mode="Markdown")


async def process_photo_batch(unique_key, user_id, level, ssd, exam_type, year, update, context):
    await asyncio.sleep(3)

    async with pending_photo_batches[unique_key]["lock"]:
        batch = pending_photo_batches[unique_key]
        file_ids = batch["file_ids"].copy()
        batch["file_ids"] = []
        batch["task"] = None

    if not file_ids:
        return

    storage_key = get_storage_key(level, ssd, exam_type, year)
    nickname = get_nickname(user_id)

    new_batch = {
        "files": [{"file_id": fid, "file_type": "photo"} for fid in file_ids],
        "uploader": nickname,
        "uploader_id": user_id,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d"),
        "ratings": {"up": 0, "down": 0}
    }

    if storage_key not in exam_vault:
        exam_vault[storage_key] = []
    exam_vault[storage_key].append(new_batch)
    save_vault()

    user_profiles[str(user_id)]["upload_count"] = user_profiles[str(user_id)].get("upload_count", 0) + len(file_ids)
    save_profiles()

    await update.message.reply_text(
        f"✅ **Saved {len(file_ids)} photo(s)!**\n\n"
        f"👤 Uploaded by: **{nickname}**\n"
        f"📝 Exam Type: **{exam_type}**\n"
        f"📅 Year: **{year}**",
        parse_mode="Markdown"
    )
    await ask_for_more(update, context)
    await notify_admin(update, context, user_id, level, ssd, exam_type, year, len(file_ids), "Photos")
    asyncio.create_task(backup_files_to_channel(context, storage_key, new_batch))


async def handle_pdf(update, context, user_id, level, ssd, exam_type, year):
    file_id = update.message.document.file_id
    storage_key = get_storage_key(level, ssd, exam_type, year)
    nickname = get_nickname(user_id)

    new_batch = {
        "files": [{"file_id": file_id, "file_type": "pdf"}],
        "uploader": nickname,
        "uploader_id": user_id,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d"),
        "ratings": {"up": 0, "down": 0}
    }

    if storage_key not in exam_vault:
        exam_vault[storage_key] = []
    exam_vault[storage_key].append(new_batch)
    save_vault()

    user_profiles[str(user_id)]["upload_count"] = user_profiles[str(user_id)].get("upload_count", 0) + 1
    save_profiles()

    await update.message.reply_text(
        f"✅ **PDF Saved!**\n\n"
        f"👤 Uploaded by: **{nickname}**\n"
        f"📝 Exam Type: **{exam_type}**\n"
        f"📅 Year: **{year}**",
        parse_mode="Markdown"
    )
    await ask_for_more(update, context)
    await notify_admin(update, context, user_id, level, ssd, exam_type, year, 1, "PDF")
    asyncio.create_task(backup_files_to_channel(context, storage_key, new_batch))


async def ask_for_more(update, context):
    keyboard = [
        [InlineKeyboardButton("📤 Yes, same subject", callback_data="more_same")],
        [InlineKeyboardButton("📤 Yes, different subject", callback_data="more_different")],
        [InlineKeyboardButton("🙅 No, that's all for now", callback_data="more_done")]
    ]
    await update.message.reply_text(
        "📎 **Do you have other documents to upload?**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def notify_admin(update, context, user_id, level, ssd, exam_type, year, count, file_type):
    if not ADMIN_CHAT_ID:
        return
    try:
        nickname = get_nickname(user_id)
        storage_key = get_storage_key(level, ssd, exam_type, year)
        total = total_file_count(exam_vault.get(storage_key, []))
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"📥 **New Upload**\n\n"
                f"👤 {nickname} (ID: {user_id})\n"
                f"📂 {level} - {ssd}\n"
                f"📝 {exam_type} ({year})\n"
                f"📄 {file_type}: {count} file(s)\n"
                f"📦 Total for this key: {total}"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Admin notification failed: {e}")


async def backup_files_to_channel(context, storage_key, batch):
    if not BACKUP_CHANNEL_ID:
        return
    try:
        uploader = batch.get("uploader", "Anonymous")
        date = batch.get("uploaded_at", "unknown")
        caption = (
            f"🗂 **BACKUP**\n"
            f"🔑 `{storage_key}`\n"
            f"👤 {uploader} · {date}"
        )
        for i, file_info in enumerate(batch["files"]):
            file_id = file_info["file_id"]
            file_type = file_info.get("file_type", "unknown")
            cap = caption if i == 0 else None
            try:
                if file_type == "photo":
                    await context.bot.send_photo(
                        chat_id=BACKUP_CHANNEL_ID, photo=file_id, caption=cap, parse_mode="Markdown"
                    )
                else:
                    await context.bot.send_document(
                        chat_id=BACKUP_CHANNEL_ID, document=file_id, caption=cap, parse_mode="Markdown"
                    )
            except Exception:
                try:
                    await context.bot.send_document(
                        chat_id=BACKUP_CHANNEL_ID, document=file_id, caption=cap, parse_mode="Markdown"
                    )
                except Exception as e:
                    logging.error(f"Backup file send failed: {e}")
    except Exception as e:
        logging.error(f"Backup to channel failed: {e}")


# --- TEXT HANDLER ---

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    session = user_sessions.get(user_id, {})

    # --- NICKNAME REGISTRATION ---
    if session.get("waiting_for_nickname"):
        if len(text) < 2:
            await update.message.reply_text("⚠️ Please enter at least 2 characters for your nickname.")
            return
        if len(text) > 30:
            await update.message.reply_text("⚠️ Nickname too long! Please keep it under 30 characters.")
            return

        nickname = text
        user_profiles[str(user_id)] = {
            "nickname": nickname,
            "registered_at": datetime.now().strftime("%Y-%m-%d"),
            "upload_count": 0
        }
        save_profiles()
        user_sessions[user_id] = {}

        await update.message.reply_text(
            f"✅ You're all set, {nickname}!\n"
            f"Let's get started. 👇",
            parse_mode="Markdown"
        )
        await show_main_menu(update, context, user_id)
        return

    # --- YEAR INPUT ---
    if session.get("waiting_for_year"):
        try:
            year = int(text)
            if 2000 <= year <= 2100:
                session["year"] = str(year)
                session["waiting_for_year"] = False
                await update.message.reply_text(
                    f"✅ Year set to **{year}**\n\nNow send your PDF or photos!",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("⚠️ Please enter a valid year between 2000 and 2100.")
        except ValueError:
            await update.message.reply_text("⚠️ Please enter a valid year (e.g., 2024)")
        return

    await update.message.reply_text("🤖 Use /start to access the main menu!")


# --- ERROR HANDLER ---

async def error_handler(update, context):
    import telegram.error as tg_err
    if isinstance(context.error, tg_err.Conflict):
        print("⚠️  Conflict detected (another instance running). Stopping this instance.")
        raise SystemExit(1)
    print(f"❌ Unhandled error: {context.error}")


# --- FLASK WEB SERVER FOR RENDER ---

from flask import Flask
import threading

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ UNICAS Exam Vault Bot is running!"

def run_web_server():
    flask_app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_web_server, daemon=True).start()


# --- MAIN ---

def main():
    print("🌐 Web server started on port 10000")
    app = Application.builder().token(TOKEN).build()
    app.add_error_handler(error_handler)

    # Basic commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))

    # Nickname management commands
    app.add_handler(CommandHandler("setname", setname_command))
    app.add_handler(CommandHandler("myprofile", myprofile_command))
    app.add_handler(CommandHandler("delete_me", delete_me_command))

    # Admin commands
    app.add_handler(CommandHandler("admin", admin_enhanced_command))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("userinfo", userinfo_command))
    app.add_handler(CommandHandler("delete_user", delete_user_command))
    app.add_handler(CommandHandler("backup", backup_command))
    app.add_handler(CommandHandler("list", admin_list))

    # Channel backup commands
    app.add_handler(CommandHandler("testchannel", testchannel_command))
    app.add_handler(CommandHandler("backfill", backfill_command))

    # Replace command
    app.add_handler(CommandHandler("replace", replace_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    # Tip command
    app.add_handler(CommandHandler("tip", tip_command))

    # Callback handlers
    app.add_handler(CallbackQueryHandler(confirm_delete_callback, pattern="^confirm_delete_"))
    app.add_handler(CallbackQueryHandler(handle_buttons))

    # Message handlers
    app.add_handler(MessageHandler(filters.Document.ALL, handle_files))
    app.add_handler(MessageHandler(filters.PHOTO, handle_files))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 UNICAS Exam Vault Bot is running!")
    print(f"📊 Loaded {len(exam_vault)} subjects | {len(user_profiles)} users")
    print("✅ Press Ctrl+C to stop")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()