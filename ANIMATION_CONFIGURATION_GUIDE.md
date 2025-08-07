# Fixation Animation Configuration Guide

## Animation Types

### 1. CSS Animation (Default - Recommended)
- **Setting**: `FIXATION_ANIMATION_TYPE = "css"`
- **Best for**: General use, development, flexible timing
- **Performance**: Excellent (60fps, minimal CPU)
- **Requirements**: None (built-in)

### 2. GIF Animation (Premium Option)
- **Setting**: `FIXATION_ANIMATION_TYPE = "gif"`
- **Best for**: Production, perfect smoothness, zero CPU impact
- **Performance**: Perfect (30fps, zero CPU during animation)
- **Requirements**: GIF files in assets/animations/

### 3. Legacy Animation (Not Recommended)
- **Setting**: `FIXATION_ANIMATION_TYPE = "legacy"`
- **Best for**: Debugging/fallback only
- **Performance**: Poor (10fps, high CPU)
- **Requirements**: None (built-in)

## Configuration Steps

1. **Edit config/settings.py**:
   ```python
   FIXATION_ANIMATION_TYPE = "css"  # or "gif" or "legacy"
   ```

2. **For GIF animations, generate files**:
   ```bash
   python create_fixation_gif.py
   ```

3. **Test the configuration**:
   ```bash  
   python test_animation_comparison.py
   python run_app.py
   ```

## Performance Comparison

| Feature | GIF | CSS | Legacy |
|---------|-----|-----|--------|
| Smoothness | Perfect | Excellent | Poor |
| CPU Usage | Zero | Minimal | High |
| File Size | ~70KB | 0KB | 0KB |
| Pregeneration Impact | None | None | High |
| Customization | Limited | High | High |

## Troubleshooting

### GIF Animation Issues
- Ensure GIF files exist in `assets/animations/`
- Check file permissions
- Verify base64 encoding works

### CSS Animation Issues  
- Check browser CSS support
- Verify JavaScript timer functionality
- Test in different browsers

### Legacy Animation Issues
- High CPU usage is expected
- Animation may stutter during pregeneration
- Consider switching to CSS or GIF

## Recommendations

- **Development**: Use CSS animation
- **Production**: Use GIF animation for best user experience
- **Fallback**: Legacy animation only if others fail
