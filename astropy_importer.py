
try:
    from astropy.wcs import WCS
except ImportError:
    # If matplotlib is not installed, we can still use WCS, but not the plotting features.
    # This workaround prevents the application from crashing.
    from astropy.wcs import WCS as WCS_core
    
    class WCS(WCS_core):
        def plot(self, *args, **kwargs):
            raise ImportError("Plotting requires matplotlib to be installed.")

        def _get_coords_overlay(self, *args, **kwargs):
            raise ImportError("Plotting requires matplotlib to be installed.")
