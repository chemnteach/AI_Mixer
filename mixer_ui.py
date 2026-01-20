"""Streamlit UI for The Mixer - AI-Powered Audio Mashup Pipeline.

Run with: streamlit run mixer_ui.py
"""

import streamlit as st
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from mixer.workflow import run_mashup_workflow
from mixer.agents import ingest_song, profile_audio, find_match
from mixer.memory import get_client, get_song, get_all_songs, delete_song
from mixer.config import get_config

# Page configuration
st.set_page_config(
    page_title="The Mixer 🎵",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'mashup_result' not in st.session_state:
    st.session_state.mashup_result = None
if 'last_ingested' not in st.session_state:
    st.session_state.last_ingested = None


def save_uploaded_file(uploaded_file) -> str:
    """Save uploaded file to temporary location and return path."""
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name


def format_metadata(metadata: dict) -> str:
    """Format song metadata for display."""
    return f"""
    **BPM:** {metadata.get('bpm', 'N/A')}
    **Key:** {metadata.get('key', 'N/A')} ({metadata.get('camelot', 'N/A')})
    **Genre:** {metadata.get('genre', 'N/A')}
    **Mood:** {metadata.get('mood_summary', 'N/A')}
    **Energy:** {metadata.get('energy', 'N/A')}/10
    **Duration:** {metadata.get('duration', 'N/A')}s
    """


def create_mashup_tab():
    """Create Mashup tab - main workflow interface."""
    st.header("🎵 Create Mashup")

    # Mode selection
    mode = st.radio(
        "Select Mode",
        ["Automatic (Recommended)", "Manual"],
        horizontal=True,
        help="Automatic: Upload one song, we'll find the perfect match. Manual: You choose both songs."
    )

    if mode == "Automatic (Recommended)":
        automatic_mode()
    else:
        manual_mode()


def automatic_mode():
    """Automatic mashup creation - upload one song, auto-match."""
    st.subheader("Automatic Mashup Creation")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Upload a song (MP3, WAV, FLAC)",
            type=['mp3', 'wav', 'flac'],
            help="Upload one song, and we'll find the best match from your library"
        )

    with col2:
        mashup_type = st.selectbox(
            "Mashup Type",
            ["Auto-Recommend", "Classic", "Stem Swap", "Energy Matched",
             "Adaptive Harmony", "Theme Fusion", "Semantic-Aligned",
             "Role-Aware", "Conversational"],
            help="Auto-Recommend: We'll choose the best type for you"
        )

    output_format = st.selectbox("Output Format", ["mp3", "wav"], index=0)

    if uploaded_file and st.button("🚀 Create Mashup", type="primary"):
        # Save uploaded file
        input_path = save_uploaded_file(uploaded_file)

        try:
            with st.spinner("Creating your mashup... This may take a few minutes."):
                # Map UI mashup type to enum value
                type_mapping = {
                    "Auto-Recommend": None,
                    "Classic": "CLASSIC",
                    "Stem Swap": "STEM_SWAP",
                    "Energy Matched": "ENERGY_MATCHED",
                    "Adaptive Harmony": "ADAPTIVE_HARMONY",
                    "Theme Fusion": "THEME_FUSION",
                    "Semantic-Aligned": "SEMANTIC_ALIGNED",
                    "Role-Aware": "ROLE_AWARE",
                    "Conversational": "CONVERSATIONAL"
                }

                # Run workflow
                result = run_mashup_workflow(
                    input_source_a=input_path,
                    input_source_b=None,  # Auto-match
                    mashup_type=type_mapping[mashup_type],
                    stream=False
                )

                if result['status'] == 'completed':
                    st.session_state.mashup_result = result
                    st.success("✅ Mashup created successfully!")

                    # Display result
                    st.subheader("Your Mashup")
                    st.audio(result['mashup_output_path'])

                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Song A:** {result['song_a_id']}")
                    with col2:
                        st.info(f"**Song B:** {result['song_b_id']}")

                    st.info(f"**Mashup Type:** {result.get('approved_mashup_type', 'N/A')}")

                    # Download button
                    with open(result['mashup_output_path'], 'rb') as f:
                        st.download_button(
                            "💾 Download Mashup",
                            f,
                            file_name=Path(result['mashup_output_path']).name,
                            mime=f"audio/{output_format}"
                        )
                else:
                    st.error(f"❌ Mashup creation failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
        finally:
            # Cleanup temp file
            Path(input_path).unlink(missing_ok=True)


def manual_mode():
    """Manual mashup creation - user selects both songs."""
    st.subheader("Manual Mashup Creation")

    # Get all songs from library
    all_songs = get_all_songs()
    song_ids = [song['id'] for song in all_songs]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Song A (Vocal Source)**")
        song_a_option = st.radio(
            "Select Song A",
            ["Upload New", "From Library"],
            key="song_a_source"
        )

        if song_a_option == "Upload New":
            song_a_file = st.file_uploader("Upload Song A", type=['mp3', 'wav', 'flac'], key="song_a_upload")
            song_a_id = None
        else:
            if song_ids:
                song_a_id = st.selectbox("Choose Song A", song_ids, key="song_a_select")
                song_a_file = None
                # Show metadata
                song_a_data = get_song(song_a_id)
                if song_a_data:
                    with st.expander("Song A Details"):
                        st.markdown(format_metadata(song_a_data['metadata']))
            else:
                st.warning("Library is empty. Please upload or ingest songs first.")
                song_a_id = None
                song_a_file = None

    with col2:
        st.markdown("**Song B (Instrumental Source)**")
        song_b_option = st.radio(
            "Select Song B",
            ["Upload New", "From Library"],
            key="song_b_source"
        )

        if song_b_option == "Upload New":
            song_b_file = st.file_uploader("Upload Song B", type=['mp3', 'wav', 'flac'], key="song_b_upload")
            song_b_id = None
        else:
            if song_ids:
                song_b_id = st.selectbox("Choose Song B", song_ids, key="song_b_select")
                song_b_file = None
                # Show metadata
                song_b_data = get_song(song_b_id)
                if song_b_data:
                    with st.expander("Song B Details"):
                        st.markdown(format_metadata(song_b_data['metadata']))
            else:
                st.warning("Library is empty. Please upload or ingest songs first.")
                song_b_id = None
                song_b_file = None

    # Mashup options
    col1, col2 = st.columns(2)
    with col1:
        mashup_type = st.selectbox(
            "Mashup Type",
            ["Classic", "Stem Swap", "Energy Matched", "Adaptive Harmony",
             "Theme Fusion", "Semantic-Aligned", "Role-Aware", "Conversational"]
        )
    with col2:
        output_format = st.selectbox("Output Format", ["mp3", "wav"], index=0)

    # Create mashup button
    if st.button("🎵 Create Mashup", type="primary"):
        # Determine song paths
        song_a_path = None
        song_b_path = None
        temp_files = []

        try:
            # Handle Song A
            if song_a_file:
                song_a_path = save_uploaded_file(song_a_file)
                temp_files.append(song_a_path)
            elif song_a_id:
                song_a_data = get_song(song_a_id)
                song_a_path = song_a_data['metadata'].get('source_path') or song_a_data['metadata'].get('cache_path')

            # Handle Song B
            if song_b_file:
                song_b_path = save_uploaded_file(song_b_file)
                temp_files.append(song_b_path)
            elif song_b_id:
                song_b_data = get_song(song_b_id)
                song_b_path = song_b_data['metadata'].get('source_path') or song_b_data['metadata'].get('cache_path')

            if not song_a_path or not song_b_path:
                st.error("❌ Please select or upload both songs")
                return

            with st.spinner("Creating mashup... This may take a few minutes."):
                # Map UI mashup type to enum value
                type_mapping = {
                    "Classic": "CLASSIC",
                    "Stem Swap": "STEM_SWAP",
                    "Energy Matched": "ENERGY_MATCHED",
                    "Adaptive Harmony": "ADAPTIVE_HARMONY",
                    "Theme Fusion": "THEME_FUSION",
                    "Semantic-Aligned": "SEMANTIC_ALIGNED",
                    "Role-Aware": "ROLE_AWARE",
                    "Conversational": "CONVERSATIONAL"
                }

                # Run workflow
                result = run_mashup_workflow(
                    input_source_a=song_a_path,
                    input_source_b=song_b_path,
                    mashup_type=type_mapping[mashup_type],
                    stream=False
                )

                if result['status'] == 'completed':
                    st.session_state.mashup_result = result
                    st.success("✅ Mashup created successfully!")

                    # Display result
                    st.subheader("Your Mashup")
                    st.audio(result['mashup_output_path'])

                    # Download button
                    with open(result['mashup_output_path'], 'rb') as f:
                        st.download_button(
                            "💾 Download Mashup",
                            f,
                            file_name=Path(result['mashup_output_path']).name,
                            mime=f"audio/{output_format}"
                        )
                else:
                    st.error(f"❌ Mashup creation failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
        finally:
            # Cleanup temp files
            for temp_file in temp_files:
                Path(temp_file).unlink(missing_ok=True)


def library_tab():
    """Library Management tab - view, search, ingest songs."""
    st.header("📚 Library Management")

    # Tabs within library
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["Browse", "Ingest", "Stats"])

    with sub_tab1:
        browse_library()

    with sub_tab2:
        ingest_interface()

    with sub_tab3:
        library_stats()


def browse_library():
    """Browse and search library."""
    st.subheader("Browse Songs")

    # Get all songs
    all_songs = get_all_songs()

    if not all_songs:
        st.info("📭 Library is empty. Go to the 'Ingest' tab to add songs.")
        return

    # Search box
    search_query = st.text_input("🔍 Search by artist, title, genre, or mood", "")

    # Filter songs
    if search_query:
        filtered_songs = [
            song for song in all_songs
            if search_query.lower() in song['id'].lower() or
               search_query.lower() in str(song['metadata'].get('genre', '')).lower() or
               search_query.lower() in str(song['metadata'].get('mood_summary', '')).lower()
        ]
    else:
        filtered_songs = all_songs

    st.write(f"Showing {len(filtered_songs)} of {len(all_songs)} songs")

    # Display songs in a grid
    for i in range(0, len(filtered_songs), 2):
        cols = st.columns(2)

        for j, col in enumerate(cols):
            if i + j < len(filtered_songs):
                song = filtered_songs[i + j]
                with col:
                    with st.container():
                        st.markdown(f"### {song['id']}")
                        st.markdown(format_metadata(song['metadata']))

                        # Action buttons
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("🔍 Analyze", key=f"analyze_{song['id']}"):
                                with st.spinner(f"Analyzing {song['id']}..."):
                                    try:
                                        cache_path = song['metadata'].get('cache_path')
                                        if cache_path:
                                            profile_audio(cache_path)
                                            st.success("✅ Analysis complete!")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error: {str(e)}")

                        with btn_col2:
                            if st.button("🗑️ Delete", key=f"delete_{song['id']}"):
                                if st.session_state.get(f"confirm_delete_{song['id']}", False):
                                    delete_song(song['id'])
                                    st.success(f"Deleted {song['id']}")
                                    st.rerun()
                                else:
                                    st.session_state[f"confirm_delete_{song['id']}"] = True
                                    st.warning("Click again to confirm deletion")

                        st.divider()


def ingest_interface():
    """Interface for ingesting new songs."""
    st.subheader("Ingest New Songs")

    ingest_mode = st.radio(
        "Ingest Mode",
        ["Upload File", "YouTube URL", "Batch Folder"],
        horizontal=True
    )

    if ingest_mode == "Upload File":
        uploaded_file = st.file_uploader(
            "Upload audio file",
            type=['mp3', 'wav', 'flac'],
            help="Upload a local audio file to add to your library"
        )

        if uploaded_file and st.button("📥 Ingest File"):
            temp_path = save_uploaded_file(uploaded_file)

            try:
                with st.spinner("Ingesting file..."):
                    result = ingest_song(temp_path)
                    st.session_state.last_ingested = result['id']

                    if result['cached']:
                        st.info(f"ℹ️ Song already in library: {result['id']}")
                    else:
                        st.success(f"✅ Successfully ingested: {result['id']}")

                    # Auto-analyze option
                    if st.checkbox("Analyze now?", value=True):
                        with st.spinner("Analyzing..."):
                            cache_path = get_song(result['id'])['metadata']['cache_path']
                            profile_audio(cache_path)
                            st.success("✅ Analysis complete!")

            except Exception as e:
                st.error(f"❌ Ingestion failed: {str(e)}")
            finally:
                Path(temp_path).unlink(missing_ok=True)

    elif ingest_mode == "YouTube URL":
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Enter a YouTube video URL to download and ingest"
        )

        if youtube_url and st.button("📥 Ingest from YouTube"):
            try:
                with st.spinner("Downloading and ingesting from YouTube..."):
                    result = ingest_song(youtube_url)
                    st.session_state.last_ingested = result['id']

                    if result['cached']:
                        st.info(f"ℹ️ Song already in library: {result['id']}")
                    else:
                        st.success(f"✅ Successfully ingested: {result['id']}")

                    # Auto-analyze option
                    if st.checkbox("Analyze now?", value=True, key="yt_analyze"):
                        with st.spinner("Analyzing..."):
                            cache_path = get_song(result['id'])['metadata']['cache_path']
                            profile_audio(cache_path)
                            st.success("✅ Analysis complete!")

            except Exception as e:
                st.error(f"❌ Ingestion failed: {str(e)}")

    else:  # Batch Folder
        st.markdown("""
        **Batch ingest all audio files from a folder** (perfect for CD rips!)

        Supported formats: MP3, WAV, FLAC, M4A, OGG
        """)

        folder_path = st.text_input(
            "Folder Path",
            placeholder=r"C:\Users\YourName\Music\New Rips",
            help="Enter the full path to a folder containing audio files"
        )

        auto_analyze = st.checkbox(
            "Analyze all songs after ingestion?",
            value=True,
            key="batch_analyze",
            help="Recommended: Extract BPM, key, lyrics, and sections for better mashups"
        )

        if folder_path and st.button("📥 Batch Ingest Folder"):
            folder = Path(folder_path)

            if not folder.exists():
                st.error(f"❌ Folder does not exist: {folder_path}")
                return

            if not folder.is_dir():
                st.error(f"❌ Path is not a folder: {folder_path}")
                return

            # Find audio files
            audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.ogg'}
            audio_files = []

            for ext in audio_extensions:
                audio_files.extend(folder.glob(f"*{ext}"))
                audio_files.extend(folder.glob(f"*{ext.upper()}"))

            if not audio_files:
                st.warning(f"⚠️ No audio files found in {folder_path}")
                return

            st.info(f"Found {len(audio_files)} audio files")

            # Ingest files
            ingested = []
            skipped = []
            failed = []

            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, audio_file in enumerate(audio_files):
                status_text.text(f"Ingesting: {audio_file.name}")

                try:
                    result = ingest_song(str(audio_file))

                    if result['cached']:
                        skipped.append(audio_file.name)
                    else:
                        ingested.append(result['id'])

                except Exception as e:
                    failed.append((audio_file.name, str(e)))

                progress_bar.progress((i + 1) / len(audio_files))

            status_text.empty()
            progress_bar.empty()

            # Summary
            st.markdown("### Ingestion Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Ingested", len(ingested))
            with col2:
                st.metric("⚠️ Skipped", len(skipped))
            with col3:
                st.metric("❌ Failed", len(failed))

            if failed:
                with st.expander("Show failed files"):
                    for filename, error in failed:
                        st.text(f"- {filename}: {error}")

            # Auto-analyze
            if auto_analyze and ingested:
                st.markdown("### Analyzing Songs")

                analyzed = 0
                analysis_failed = 0

                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, song_id in enumerate(ingested):
                    status_text.text(f"Analyzing: {song_id}")

                    try:
                        song_data = get_song(song_id)
                        if song_data:
                            profile_audio(song_data['metadata']['cache_path'])
                            analyzed += 1
                    except Exception as e:
                        analysis_failed += 1

                    progress_bar.progress((i + 1) / len(ingested))

                status_text.empty()
                progress_bar.empty()

                st.success(f"✅ Analyzed {analyzed} songs")
                if analysis_failed:
                    st.warning(f"⚠️ {analysis_failed} analysis failures")

            st.success("🎉 Batch ingestion complete!")


def library_stats():
    """Display library statistics."""
    st.subheader("Library Statistics")

    all_songs = get_all_songs()

    if not all_songs:
        st.info("📭 Library is empty.")
        return

    # Basic stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Songs", len(all_songs))

    with col2:
        analyzed = sum(1 for song in all_songs if song['metadata'].get('sections'))
        st.metric("Analyzed", analyzed)

    with col3:
        total_duration = sum(song['metadata'].get('duration', 0) for song in all_songs)
        st.metric("Total Duration", f"{total_duration/60:.1f} min")

    with col4:
        avg_bpm = sum(song['metadata'].get('bpm', 0) for song in all_songs if song['metadata'].get('bpm')) / len(all_songs)
        st.metric("Avg BPM", f"{avg_bpm:.0f}")

    # Genre distribution
    st.subheader("Genre Distribution")
    genres = {}
    for song in all_songs:
        genre = song['metadata'].get('genre', 'Unknown')
        genres[genre] = genres.get(genre, 0) + 1

    if genres:
        st.bar_chart(genres)

    # Key distribution
    st.subheader("Key Distribution")
    keys = {}
    for song in all_songs:
        key = song['metadata'].get('key', 'Unknown')
        keys[key] = keys.get(key, 0) + 1

    if keys:
        st.bar_chart(keys)


def settings_tab():
    """Settings tab - view and edit configuration."""
    st.header("⚙️ Settings")

    config = get_config()

    st.subheader("Audio Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Sample Rate", value=str(config.get("audio.sample_rate")), disabled=True)
        st.text_input("Bit Depth", value=str(config.get("audio.bit_depth")), disabled=True)
    with col2:
        st.text_input("Channels", value=str(config.get("audio.channels")), disabled=True)
        st.text_input("Quality", value=config.get("audio.quality"), disabled=True)

    st.subheader("Model Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Whisper Model", value=config.get("whisper.model_size"), disabled=True)
        st.text_input("LLM Provider", value=config.get("llm.provider"), disabled=True)
    with col2:
        st.text_input("Demucs Model", value=config.get("demucs.model"), disabled=True)
        st.text_input("Claude Model", value=config.get("llm.anthropic_model"), disabled=True)

    st.subheader("Curator Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("BPM Tolerance", value=str(config.get("curator.bpm_tolerance")), disabled=True)
        st.text_input("BPM Weight", value=str(config.get("curator.weight_bpm")), disabled=True)
    with col2:
        st.text_input("Max Stretch Ratio", value=str(config.get("curator.max_stretch_ratio")), disabled=True)
        st.text_input("Key Weight", value=str(config.get("curator.weight_key")), disabled=True)

    st.info("💡 To modify settings, edit `config.yaml` in the project root directory.")


def main():
    """Main application."""
    # Sidebar
    with st.sidebar:
        st.title("🎵 The Mixer")
        st.markdown("AI-Powered Audio Mashup Pipeline")
        st.divider()

        # Quick stats
        all_songs = get_all_songs()
        st.metric("Library Size", len(all_songs))

        st.divider()

        # About
        with st.expander("ℹ️ About"):
            st.markdown("""
            **The Mixer** uses AI to create intelligent audio mashups.

            **Features:**
            - 8 mashup types (Classic, Conversational, etc.)
            - Semantic song matching
            - Automatic song pairing
            - Section-level analysis

            **How to use:**
            1. Ingest songs into your library
            2. Create mashups (auto or manual mode)
            3. Download and enjoy!
            """)

        with st.expander("🎨 Mashup Types"):
            st.markdown("""
            - **Classic:** Vocal + instrumental swap
            - **Stem Swap:** Exchange instruments
            - **Energy Matched:** Align by energy levels
            - **Adaptive Harmony:** Dynamic mixing
            - **Theme Fusion:** Lyrical coherence
            - **Semantic-Aligned:** Emotional arcs
            - **Role-Aware:** Q&A vocal dynamics
            - **Conversational:** Dialogue flow
            """)

    # Main tabs
    tab1, tab2, tab3 = st.tabs(["🎵 Create Mashup", "📚 Library", "⚙️ Settings"])

    with tab1:
        create_mashup_tab()

    with tab2:
        library_tab()

    with tab3:
        settings_tab()


if __name__ == "__main__":
    main()
