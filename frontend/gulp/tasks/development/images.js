var gulp         = require('gulp');
var config       = require('../../config');

// copy images
gulp.task('images', function(callback) {
   return gulp.src(config.images.src)
      .pipe(gulp.dest(config.images.dest));
});
