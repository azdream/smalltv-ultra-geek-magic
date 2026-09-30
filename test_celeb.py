import renderer
import io

r = renderer.RetroDashboardRenderer()
gif_bytes = r.render_animated_celebration(app_name="TestApp", count=5, title="Test Title")
with open("test_cel.gif", "wb") as f:
    f.write(gif_bytes)
