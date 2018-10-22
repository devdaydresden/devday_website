var gulp         = require('gulp');
var config       = require('../../config');

gulp.task('jquery', function(callback) {
   return gulp.src(config.jquery.src)
      .pipe(gulp.dest(config.jquery.dest));
});
