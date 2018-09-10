var gulp         = require('gulp');
var sass         = require('gulp-sass');
var cssnano      = require('gulp-cssnano');
var sourcemaps   = require('gulp-sourcemaps');
var autoprefixer = require('gulp-autoprefixer');
var gulpif       = require('gulp-if');
var plumber      = require('gulp-plumber');
var minimist     = require('minimist');
var header       = require('gulp-header');
var config       = require('../../config');
var browserSync  = require('browser-sync');

var options         = minimist(process.argv.slice(2), config.environment);

// compile sass files to one css file
// write sourcemaps and minify if param production is set
gulp.task('sass', function () {
    return gulp.src(config.sass.src)
        .pipe(gulpif(options.env === config.environment.production, sourcemaps.init({
            loadMaps: true
        }))) // init source maps in production
        .pipe(plumber())
        .pipe(sass())
        .pipe(header(config.strings.banner))
        .pipe(autoprefixer(config.sass.options.autoprefixer))
        .pipe(gulpif(options.env === config.environment.production, cssnano())) // only minify in production
        .pipe(gulpif(options.env === config.environment.production, sourcemaps.write('.'))) //write sourcemap in production
        .pipe(gulp.dest(config.sass.dest));
});

gulp.task('sass-bs', function () {
    return gulp.src(config.sass.src)
        .pipe(gulpif(options.env === config.environment.production, sourcemaps.init({
            loadMaps: true
        }))) // init source maps in production
        .pipe(plumber())
        .pipe(sass())
        .pipe(header(config.strings.banner))
        .pipe(autoprefixer(config.sass.options.autoprefixer))
        .pipe(gulpif(options.env === config.environment.production, cssnano())) // only minify in production
        .pipe(gulpif(options.env === config.environment.production, sourcemaps.write('.'))) //write sourcemap in production
        .pipe(gulp.dest(config.sass.dest))
        .pipe(browserSync.stream());
});
