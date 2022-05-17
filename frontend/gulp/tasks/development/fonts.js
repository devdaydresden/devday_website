var gulp            = require('gulp');
var config          = require('../../config');

function build_fonts() {
    return gulp.src(config.fonts.src)
        .pipe(gulp.dest(config.fonts.dest));
}
