"""
Web application for Speech Emotion Detection.
Provides both Flask REST API and Streamlit dashboard.

Usage:
  # Run Flask API
  python app.py --mode api --port 5000
  
  # Run Streamlit dashboard
  streamlit run app.py
"""

import sys
import os
import argparse
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_flask_api(port=5000):
    """Run Flask REST API server."""
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import json
    import tempfile
    from emotion_detection import EmotionDetectionPipeline
    
    # Initialize Flask app
    app = Flask(__name__)
    CORS(app)
    
    # Initialize pipeline
    print("Initializing Emotion Detection Pipeline...")
    pipeline = EmotionDetectionPipeline('config.yaml')
    print("Pipeline ready!")
    
    # Optional: MQTT client for ESP32
    mqtt_client = None
    if pipeline.config['mqtt']['enabled']:
        try:
            import paho.mqtt.client as mqtt
            
            mqtt_client = mqtt.Client()
            mqtt_client.connect(
                pipeline.config['mqtt']['broker'],
                pipeline.config['mqtt']['port'],
                60
            )
            mqtt_client.loop_start()
            print(f"MQTT client connected to {pipeline.config['mqtt']['broker']}")
        except Exception as e:
            print(f"Warning: MQTT connection failed: {e}")
    
    @app.route('/', methods=['GET'])
    def home():
        """Health check endpoint."""
        return jsonify({
            'status': 'ok',
            'service': 'AffectiveCore Speech Emotion Detection',
            'version': '1.0',
            'endpoints': {
                '/analyze': 'POST - Analyze audio file',
                '/health': 'GET - Health check',
                '/stats': 'GET - Performance statistics'
            }
        })
    
    @app.route('/health', methods=['GET'])
    def health():
        """Detailed health check."""
        return jsonify({
            'status': 'healthy',
            'pipeline': 'ready',
            'mqtt_enabled': pipeline.config['mqtt']['enabled'],
            'mqtt_connected': mqtt_client is not None
        })
    
    @app.route('/analyze', methods=['POST'])
    def analyze():
        """
        Analyze audio file endpoint.
        
        Expects:
          - file: audio file (multipart/form-data)
          - compress: optional boolean for compressed output
        
        Returns:
          - JSON with emotion analysis result
        """
        try:
            # Check if file is present
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'error': 'Empty filename'}), 400
            
            # Get options
            compress = request.form.get('compress', 'false').lower() == 'true'
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(
                suffix=Path(file.filename).suffix,
                delete=False
            ) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name
            
            try:
                # Analyze
                result = pipeline.analyze_audio_file(tmp_path)
                
                # Compress if requested
                if compress:
                    result = pipeline.get_compressed_output(result)
                
                # Publish to MQTT if enabled
                if mqtt_client and not result['notes'].get('error'):
                    try:
                        topic = pipeline.config['mqtt']['topic']
                        qos = pipeline.config['mqtt']['qos']
                        
                        # Use compressed version for MQTT
                        mqtt_payload = pipeline.get_compressed_output(result)
                        mqtt_client.publish(
                            topic,
                            json.dumps(mqtt_payload),
                            qos=qos
                        )
                    except Exception as e:
                        print(f"MQTT publish error: {e}")
                
                return jsonify(result), 200
                
            finally:
                # Clean up temp file
                Path(tmp_path).unlink()
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/stats', methods=['GET'])
    def stats():
        """Get performance statistics."""
        return jsonify(pipeline.get_performance_stats())
    
    @app.route('/reset', methods=['POST'])
    def reset():
        """Reset pipeline state."""
        pipeline.reset()
        return jsonify({'status': 'reset'})
    
    # Run server
    print(f"\n🚀 Starting Flask API on http://0.0.0.0:{port}")
    print(f"📡 API Documentation: http://localhost:{port}/")
    app.run(host='0.0.0.0', port=port, debug=False)


def run_streamlit_dashboard():
    """Run Streamlit dashboard."""
    import streamlit as st
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    from datetime import datetime
    import json
    import tempfile
    from emotion_detection import EmotionDetectionPipeline
    
    # Page config
    st.set_page_config(
        page_title="AffectiveCore - Emotion Detection",
        page_icon="🎭",
        layout="wide"
    )
    
    # Title
    st.title("🎭 AffectiveCore: Speech Emotion Detection")
    st.markdown("**Multimodal emotion analysis from speech audio**")
    
    # Sidebar
    st.sidebar.header("⚙️ Configuration")
    
    # Initialize pipeline (with caching)
    @st.cache_resource
    def load_pipeline():
        return EmotionDetectionPipeline('config.yaml')
    
    try:
        pipeline = load_pipeline()
        st.sidebar.success("✅ Pipeline loaded")
    except Exception as e:
        st.sidebar.error(f"❌ Pipeline error: {e}")
        st.stop()
    
    # Options
    enable_smoothing = st.sidebar.checkbox("Enable temporal smoothing", value=False)
    show_breakdown = st.sidebar.checkbox("Show detailed breakdown", value=True)
    show_acoustic = st.sidebar.checkbox("Show acoustic features", value=True)
    
    # Reset button
    if st.sidebar.button("🔄 Reset Pipeline"):
        pipeline.reset()
        st.sidebar.success("Pipeline reset!")
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📁 File Analysis", "📊 Batch Analysis", "📈 Statistics"])
    
    # Tab 1: Single File Analysis
    with tab1:
        st.header("Upload Audio File")
        
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=['wav', 'mp3', 'flac', 'ogg', 'm4a']
        )
        
        if uploaded_file is not None:
            # Save uploaded file
            with tempfile.NamedTemporaryFile(
                suffix=Path(uploaded_file.name).suffix,
                delete=False
            ) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            
            # Show file info
            st.info(f"📄 File: {uploaded_file.name}")
            
            # Analyze button
            if st.button("🎯 Analyze Emotion", type="primary"):
                with st.spinner("Analyzing..."):
                    try:
                        result = pipeline.analyze_audio_file(
                            tmp_path,
                            enable_smoothing=enable_smoothing
                        )
                        
                        # Clean up
                        Path(tmp_path).unlink()
                        
                        # Display results
                        if result['notes'].get('error'):
                            st.error(f"❌ Error: {result['notes']['error']}")
                        else:
                            # Main result
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Emotion", result['emotion'].upper())
                            with col2:
                                st.metric("Intensity", result['intensity'])
                            with col3:
                                st.metric("Confidence", f"{result['confidence']:.1%}")
                            with col4:
                                st.metric("Latency", f"{result.get('latency', 0):.3f}s")
                            
                            # Transcription
                            st.subheader("📝 Transcription")
                            st.write(f"*\"{result['transcription']}\"*")
                            
                            # Action triggers
                            st.subheader("🎨 ESP32 Actions")
                            action = result['action_trigger']
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.info(f"💡 LED: {action['led_color']}")
                            with col2:
                                st.info(f"💬 Quote: {action['quote_category']}")
                            with col3:
                                st.info(f"🤖 Servo: {action['servo_gesture']}")
                            
                            # Breakdown
                            if show_breakdown and 'breakdown' in result:
                                st.subheader("📊 Emotion Breakdown")
                                
                                breakdown = result['breakdown']
                                
                                # Emotion comparison chart
                                emotions_data = []
                                
                                if 'text_emotion' in breakdown:
                                    for emotion, score in breakdown['text_emotion'].items():
                                        emotions_data.append({
                                            'Emotion': emotion,
                                            'Source': 'Text',
                                            'Score': score
                                        })
                                
                                if 'tone_emotion' in breakdown:
                                    for emotion, score in breakdown['tone_emotion'].items():
                                        emotions_data.append({
                                            'Emotion': emotion,
                                            'Source': 'Tone',
                                            'Score': score
                                        })
                                
                                if 'fused_emotion' in breakdown:
                                    for emotion, score in breakdown['fused_emotion'].items():
                                        emotions_data.append({
                                            'Emotion': emotion,
                                            'Source': 'Fused',
                                            'Score': score
                                        })
                                
                                if emotions_data:
                                    df_emotions = pd.DataFrame(emotions_data)
                                    
                                    fig = px.bar(
                                        df_emotions,
                                        x='Emotion',
                                        y='Score',
                                        color='Source',
                                        barmode='group',
                                        title='Emotion Scores by Source',
                                        color_discrete_map={
                                            'Text': '#1f77b4',
                                            'Tone': '#ff7f0e',
                                            'Fused': '#2ca02c'
                                        }
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            # Acoustic features
                            if show_acoustic and 'acoustic_features' in breakdown:
                                st.subheader("🎵 Acoustic Features")
                                
                                features = breakdown['acoustic_features']
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.metric("Pitch (mean)", f"{features.get('pitch_mean', 0):.1f} Hz")
                                    st.metric("Pitch (std)", f"{features.get('pitch_std', 0):.1f} Hz")
                                    st.metric("Energy", f"{features.get('energy_mean', 0):.4f}")
                                
                                with col2:
                                    st.metric("Speech Rate", f"{features.get('speech_rate', 0):.2f} syll/s")
                                    st.metric("ZCR", f"{features.get('zcr_mean', 0):.4f}")
                                    st.metric("Spectral Centroid", f"{features.get('spectral_centroid_mean', 0):.1f} Hz")
                            
                            # Notes and warnings
                            notes = result['notes']
                            if notes.get('mixed_emotion'):
                                st.warning(f"⚠️ {notes.get('mixed_emotion_details', 'Mixed emotion detected')}")
                            
                            if notes.get('fallback_mode'):
                                st.warning(f"⚠️ Fallback mode: {notes.get('reason', 'unknown')}")
                            
                            # Raw JSON
                            with st.expander("📄 View Raw JSON"):
                                st.json(result)
                    
                    except Exception as e:
                        st.error(f"❌ Analysis failed: {e}")
                        import traceback
                        st.code(traceback.format_exc())
    
    # Tab 2: Batch Analysis
    with tab2:
        st.header("Batch Analysis")
        st.write("Upload multiple audio files for batch processing")
        
        uploaded_files = st.file_uploader(
            "Choose audio files",
            type=['wav', 'mp3', 'flac', 'ogg'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} files uploaded")
            
            if st.button("🚀 Analyze Batch", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                temp_files = []
                
                for i, file in enumerate(uploaded_files):
                    status_text.text(f"Processing {file.name}...")
                    
                    # Save temp file
                    with tempfile.NamedTemporaryFile(
                        suffix=Path(file.name).suffix,
                        delete=False
                    ) as tmp:
                        tmp.write(file.read())
                        temp_files.append(tmp.name)
                    
                    # Analyze
                    try:
                        result = pipeline.analyze_audio_file(
                            temp_files[-1],
                            enable_smoothing=False
                        )
                        result['filename'] = file.name
                        results.append(result)
                    except Exception as e:
                        st.warning(f"Failed to process {file.name}: {e}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                # Clean up temp files
                for tmp_path in temp_files:
                    Path(tmp_path).unlink()
                
                status_text.text("✅ Batch analysis complete!")
                
                # Display results
                if results:
                    # Summary table
                    summary_data = []
                    for r in results:
                        summary_data.append({
                            'File': r['filename'],
                            'Emotion': r['emotion'],
                            'Intensity': r['intensity'],
                            'Confidence': r['confidence'],
                            'Latency': r.get('latency', 0)
                        })
                    
                    df_summary = pd.DataFrame(summary_data)
                    st.dataframe(df_summary, use_container_width=True)
                    
                    # Emotion distribution
                    st.subheader("📊 Emotion Distribution")
                    
                    emotion_counts = df_summary['Emotion'].value_counts()
                    fig = px.pie(
                        values=emotion_counts.values,
                        names=emotion_counts.index,
                        title='Emotion Distribution'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Download results
                    st.download_button(
                        "📥 Download Results (JSON)",
                        data=json.dumps(results, indent=2),
                        file_name="batch_results.json",
                        mime="application/json"
                    )
    
    # Tab 3: Statistics
    with tab3:
        st.header("Performance Statistics")
        
        stats = pipeline.get_performance_stats()
        
        if stats['samples'] > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Samples", stats['samples'])
            with col2:
                st.metric("Avg Latency", f"{stats['avg_latency']:.3f}s")
            with col3:
                st.metric("Max Latency", f"{stats['max_latency']:.3f}s")
            with col4:
                st.metric("Within Target", f"{stats['within_target']:.1%}")
            
            # Latency history
            if pipeline.latency_history:
                st.subheader("⏱️ Latency History")
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=pipeline.latency_history,
                    mode='lines+markers',
                    name='Latency'
                ))
                fig.add_hline(
                    y=stats['target_latency'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Target"
                )
                fig.update_layout(
                    xaxis_title="Sample",
                    yaxis_title="Latency (s)",
                    title="Latency Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No samples analyzed yet. Process some audio files to see statistics.")


if __name__ == '__main__':
    # Check if running via streamlit
    if 'streamlit' in sys.modules:
        run_streamlit_dashboard()
    else:
        parser = argparse.ArgumentParser(description='AffectiveCore Web Application')
        parser.add_argument(
            '--mode',
            choices=['api', 'dashboard'],
            default='api',
            help='Run mode: api (Flask) or dashboard (Streamlit)'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=5000,
            help='Port for Flask API (default: 5000)'
        )
        
        args = parser.parse_args()
        
        if args.mode == 'api':
            run_flask_api(args.port)
        else:
            print("For Streamlit dashboard, run: streamlit run app.py")

