# GPX Surface Analyzer

## Purpose
The GPX Surface Analyzer is a Python-based web application designed to analyze GPX tracks for their suitability for different types of biking, specifically road biking and gravel biking. It calculates:

- **Surface Types**: Breakdown of road surfaces along the route.
- **Suitability Scores**: Scores for road biking and gravel biking based on surface types.
- **Elevation Data**: Total elevation gain and loss along the route.

This tool is ideal for cyclists planning trips who need insights into route surfaces and elevation changes.

---

## Setup Instructions

### Prerequisites
- Python 3.9 or newer
- Docker (if running the application in a container)
- Task (https://taskfile.dev/)

### Local Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd gpx-surface-analyzer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Flask application:
   ```bash
   python app.py
   ```

4. The application will be available at `http://127.0.0.1:5000`.

### Using Docker

1. Build the Docker image:
   ```bash
   docker build -t gpx-surface-analyzer .
   ```

2. Run the Docker container:
   ```bash
   docker run -p 5000:5000 gpx-surface-analyzer
   ```

---

## Usage

1. Send a POST request to the `/analyze_surface` endpoint with a GPX file.
   Example using `curl`:
   ```bash
   curl -X POST -F "gpx_file=@path/to/track.gpx" http://127.0.0.1:5000/analyze_surface
   ```

2. The response will include:
   - **Surface Lengths**: A breakdown of surface types and their respective lengths (in km).
   - **Suitability Scores**: Scores for road and gravel biking.
   - **Elevation Data**: Total elevation gain and loss (in meters).

Example Response:
```json
{
  "surface_lengths_km": {
    "asphalt": 5.2,
    "gravel": 3.7,
    "unknown": 1.1
  },
  "suitability_scores": {
    "roadbike": 0.8,
    "gravelbike": 1.0
  },
  "elevation_data": {
    "elevation_up": 120.5,
    "elevation_down": 115.3
  }
}
```

---

## Next Steps and Possible Improvements

1. **Extended Surface Support**:
   - Add more granular mapping for surface types.
   - Improve handling of `unknown` surfaces by inferring based on context.

2. **Performance Optimization**:
   - Cache Overpass API results for frequently queried areas.
   - Optimize GPX parsing for large files.

3. **Enhanced Suitability Metrics**:
   - Incorporate other factors like slope and weather conditions.

4. **Frontend Integration**:
   - Build a web interface for uploading GPX files and visualizing results.

5. **Custom OSM Support**:
   - Enable querying custom OpenStreetMap instances with user-provided data.

---

## License
This project is licensed under the MIT License.

