/**
 * Photography Gallery - Immersive scroll experience with music
 * Features: scroll-snap navigation, tag-based music switching, smooth crossfades
 */

class PhotographyGallery {
  constructor() {
    this.currentAudio = document.getElementById('audio-current');
    this.nextAudio = document.getElementById('audio-next');
    this.sections = document.querySelectorAll('.photo-section');
    this.currentIndex = -1;
    this.isTransitioning = false;
    this.fadeSpeed = 1500; // milliseconds for crossfade

    // Load photo data from embedded JSON
    const dataElement = document.getElementById('photo-data');
    this.photoData = dataElement ? JSON.parse(dataElement.textContent) : { photos: [] };

    this.init();
  }

  init() {
    if (this.sections.length === 0) return;

    // Set up Intersection Observer for scroll detection
    this.setupScrollObserver();

    // Initialize audio settings
    this.currentAudio.volume = 0;
    this.nextAudio.volume = 0;

    // Add event listeners
    this.currentAudio.addEventListener('ended', () => this.handleTrackEnd(this.currentAudio));
    this.nextAudio.addEventListener('ended', () => this.handleTrackEnd(this.nextAudio));

    // Keyboard navigation
    document.addEventListener('keydown', (e) => this.handleKeyboard(e));

    // Initialize first photo's music
    this.loadInitialTrack();
  }

  setupScrollObserver() {
    const options = {
      root: null,
      rootMargin: '0px',
      threshold: 0.6 // Photo is considered "active" when 60% visible
    };

    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const section = entry.target;
          const index = parseInt(section.dataset.index);

          // Only trigger if it's a new photo
          if (index !== this.currentIndex) {
            this.onPhotoChange(section, index);
          }
        }
      });
    }, options);

    // Observe all photo sections
    this.sections.forEach(section => this.observer.observe(section));
  }

  async onPhotoChange(section, index) {
    if (this.isTransitioning) return;

    console.log(`Photo changed to index ${index}`);
    this.currentIndex = index;

    // Get track URL from section data
    const trackUrl = section.dataset.track;
    if (!trackUrl) return;

    // Switch to new track with crossfade
    await this.switchTrack(trackUrl);

    // Preload next track if available
    this.preloadNextTrack(index + 1);
  }

  async switchTrack(newTrackUrl) {
    this.isTransitioning = true;

    // Determine which audio element to use
    const [activeAudio, inactiveAudio] = this.currentAudio.volume > 0
      ? [this.currentAudio, this.nextAudio]
      : [this.nextAudio, this.currentAudio];

    // Load new track in inactive audio element
    inactiveAudio.src = newTrackUrl;
    inactiveAudio.loop = true;

    try {
      await inactiveAudio.play();
    } catch (error) {
      console.warn('Audio playback failed (user interaction may be required):', error);
      this.isTransitioning = false;
      return;
    }

    // Crossfade
    await this.crossfade(inactiveAudio, activeAudio);

    this.isTransitioning = false;
  }

  async crossfade(fadeInAudio, fadeOutAudio) {
    const steps = 30;
    const stepDuration = this.fadeSpeed / steps;

    return new Promise((resolve) => {
      let step = 0;

      const interval = setInterval(() => {
        step++;
        const progress = step / steps;

        // Fade in new track
        fadeInAudio.volume = Math.min(1, progress);

        // Fade out old track
        if (fadeOutAudio.src) {
          fadeOutAudio.volume = Math.max(0, 1 - progress);
        }

        if (step >= steps) {
          clearInterval(interval);

          // Stop and reset the old track
          if (fadeOutAudio.src) {
            fadeOutAudio.pause();
            fadeOutAudio.currentTime = 0;
            fadeOutAudio.volume = 0;
          }

          resolve();
        }
      }, stepDuration);
    });
  }

  preloadNextTrack(nextIndex) {
    if (nextIndex >= this.sections.length) return;

    const nextSection = this.sections[nextIndex];
    const nextTrackUrl = nextSection.dataset.track;

    if (nextTrackUrl) {
      // Preload in whichever audio element is currently inactive
      const inactiveAudio = this.currentAudio.volume > 0 ? this.nextAudio : this.currentAudio;
      inactiveAudio.src = nextTrackUrl;
      inactiveAudio.load();
    }
  }

  loadInitialTrack() {
    // Start with first photo's track at low volume
    if (this.sections.length > 0) {
      const firstSection = this.sections[0];
      const firstTrack = firstSection.dataset.track;

      if (firstTrack) {
        this.currentAudio.src = firstTrack;
        this.currentAudio.loop = true;
        this.currentAudio.volume = 0;

        // Auto-play on first interaction
        const startAudio = () => {
          this.currentAudio.play()
            .then(() => {
              // Fade in
              this.fadeIn(this.currentAudio);
              this.currentIndex = 0;
            })
            .catch(err => console.warn('Auto-play prevented:', err));

          // Remove listeners after first interaction
          document.removeEventListener('click', startAudio);
          document.removeEventListener('scroll', startAudio);
          document.removeEventListener('keydown', startAudio);
        };

        document.addEventListener('click', startAudio, { once: true });
        document.addEventListener('scroll', startAudio, { once: true });
        document.addEventListener('keydown', startAudio, { once: true });
      }
    }
  }

  fadeIn(audio) {
    const steps = 20;
    const stepDuration = 800 / steps;
    let step = 0;

    const interval = setInterval(() => {
      step++;
      audio.volume = Math.min(1, step / steps);

      if (step >= steps) {
        clearInterval(interval);
      }
    }, stepDuration);
  }

  handleTrackEnd(audio) {
    // Loop is enabled, but this is a fallback
    audio.currentTime = 0;
    audio.play().catch(err => console.warn('Replay failed:', err));
  }

  handleKeyboard(e) {
    // Arrow down or right: next photo
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
      e.preventDefault();
      this.scrollToPhoto(this.currentIndex + 1);
    }

    // Arrow up or left: previous photo
    if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
      e.preventDefault();
      this.scrollToPhoto(this.currentIndex - 1);
    }

    // Home: first photo
    if (e.key === 'Home') {
      e.preventDefault();
      this.scrollToPhoto(0);
    }

    // End: last photo
    if (e.key === 'End') {
      e.preventDefault();
      this.scrollToPhoto(this.sections.length - 1);
    }
  }

  scrollToPhoto(index) {
    if (index < 0 || index >= this.sections.length) return;

    this.sections[index].scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    });
  }
}

// Initialize gallery when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new PhotographyGallery();

  // Initialize Lightense for image zoom (if available)
  if (window.Lightense) {
    window.Lightense('.photo-image', {
      background: 'rgba(0, 0, 0, 0.95)'
    });
  }
});
