use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use log::{info, warn};

async fn status_handler(path: web::Path<String>) -> impl Responder {
    let (code, message) = match path.as_str() {
        "200" => {
            info!("Returning 200 OK response");
            (200, "OK")
        },
        "400" => {
            warn!("Returning 400 Bad Request response");
            (400, "Bad Request")
        },
        "500" => {
            warn!("Returning 500 Internal Server Error response");
            (500, "Internal Server Error")
        },
        unknown => {
            warn!("Unknown status code requested: {}", unknown);
            (404, "Not Found")
        },
    };

    HttpResponse::build(actix_web::http::StatusCode::from_u16(code).unwrap())
        .body(message)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init_from_env(env_logger::Env::new().default_filter_or("info"));
    info!("Starting server at 0.0.0.0:8080");

    HttpServer::new(|| {
        App::new()
            .route("/{code}", web::get().to(status_handler))
    })
    .bind("0.0.0.0:8080")?
    .run()
    .await
}
